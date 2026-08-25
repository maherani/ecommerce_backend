# PROJECT_STATE

## 1. Objective

Build a production-oriented e-commerce backend using FastAPI, PostgreSQL, Redis, SQLAlchemy, JWT authentication, Alembic, Docker, automated testing, CI/CD, caching, rate limiting, background task processing, inventory management, payment persistence, and production-readiness practices.

Every completed step must be implemented, tested, documented, committed, pushed, and verified before moving to the next step.

## 2. Current Architecture

```text
Client / Frontend
       |
       v
    FastAPI (web)
       |
       +---- User Module
       +---- Product Module
       +---- Cart Module
       +---- Order Module
       |       +---- OrderItem
       |       +---- Shipping (1:1)
       |       +---- Payment  (1:1)
       +---- Rate Limiting
       +---- Background Tasks

                 |                 |
                 v                 v
             PostgreSQL          Redis

Docker Compose:
    db ------------- PostgreSQL
    redis ---------- Redis
    web ------------ FastAPI
    celery_worker -- Celery Worker
```

## 3. Completed Steps

- Step 1 — Project setup and initial inspection
- Step 2 — Configuration and security
- Step 3 — User module
- Step 4 — PostgreSQL and authentication
- Step 5 — Alembic database migrations
- Step 6 — Dockerization and Docker Compose
- Step 7 — JWT protected routes
- Step 8 — RBAC / Admin authorization
- Step 9 — Product and Category catalog
- Step 10 — Product search, pagination, and category filtering
- Step 11 — Shopping cart
- Step 12 — Order checkout and order history
- Step 13 — Mock payment processing
- Step 14 — Pytest automated testing
- Step 15 — End-to-end shopping flow tests
- Step 16 — GitHub Actions CI
- Step 17 — Alembic schema management
- Step 18 — Redis product caching
- Step 19 — Redis-backed rate limiting
- Step 20 — Celery background worker
- Step 21 — Alembic schema reconciliation and migration-aware CI
- Step 22 — Inventory management and atomic stock reservation
- Step 23 — Order cancellation and stock restoration
- Step 24 — Order lifecycle and admin order management
- Step 25 — Shipping and delivery management
- Step 30 — Persistent payment records

## 4. Current Project Status

### Step 30 — Persistent Payment Records

Step 30 adds a persistent Payment domain entity backed by PostgreSQL.

Implemented:

- `Payment` SQLAlchemy model.
- One-to-one `Order` ↔ `Payment` relationship.
- Payment amount persistence using the order total.
- Payment status persistence.
- Unique mock transaction ID generation.
- `created_at`, `paid_at`, and `refunded_at` fields.
- Protection against paying an order that is not `pending`.
- Protection against duplicate payment processing.
- Ownership validation so users cannot pay another user's order.
- Payment record persisted before returning the successful response.
- Alembic migration `cff58edd10a9_add_payments_table.py`.

Payment endpoint:

```text
POST /payment/process
```

Current payment flow:

```text
pending order
      |
      v
POST /payment/process
      |
      +--> validate ownership
      +--> validate pending state
      +--> reject existing payment
      +--> generate transaction_id
      +--> create Payment(status=paid)
      +--> set order.status = paid
      +--> commit transaction
      |
      v
successful payment response
```

The gateway remains a mock. Real provider integration and real refund processing are not implemented yet.

### Latest Verification

```text
30 passed
```

Verification command:

```bash
docker compose exec web pytest -q
```

Migration verification:

```bash
docker compose exec web alembic current
docker compose exec db psql -U shop_admin -d ecommerce_db -c "\\d payments"
```

Expected migration head:

```text
cff58edd10a9
```

## 5. Implemented Features

### Authentication

- Registration
- Login
- Password hashing
- JWT authentication
- Current-user dependency
- Admin/superuser authorization

### Product Catalog

- Categories
- Products
- Pagination
- Search
- Category filtering
- Redis caching
- Cache invalidation
- Product stock quantity

### Cart

- User-specific cart
- Add/increment/remove
- Stock validation
- Insufficient-stock protection

### Orders

- Checkout
- Order history
- Order items
- Unit-price locking
- Atomic stock reservation with row-level locking
- Transaction rollback on failed checkout
- Pending-order cancellation
- Stock restoration on cancellation
- Order ownership validation
- Admin lifecycle management

Valid lifecycle:

```text
pending → paid → processing → shipped → delivered
   |
   └────────────→ cancelled
```

Terminal states:

```text
delivered
cancelled
```

Admin endpoint:

```text
PATCH /orders/{order_id}/status
```

### Shipping

Step 25 introduced a dedicated Shipping entity.

Fields:

```text
address
city
postal_code
carrier
tracking_number
shipped_at
delivered_at
```

Features:

- One-to-one Order ↔ Shipping relationship
- Shipping creation during checkout
- Shipping data in OrderResponse
- Admin carrier/tracking management
- `shipped_at` on transition to `shipped`
- `delivered_at` on transition to `delivered`
- Failed-checkout rollback coverage

Endpoint:

```text
PATCH /shipping/{order_id}
```

Migration:

```text
40f98fd888bb_add_shipping_table.py
```

### Payment

Step 30 introduced persistent payment records.

Payment fields:

```text
id
order_id
amount
status
transaction_id
created_at
paid_at
refunded_at
```

Migration:

```text
cff58edd10a9_add_payments_table.py
```

Database constraints include:

- Primary key on `id`
- Foreign key `order_id -> orders.id`
- Unique `order_id`
- Unique `transaction_id`

### Rate Limiting

- SlowAPI
- Redis-backed storage
- Login rate limit

### Celery

- Redis broker
- Redis result backend
- Dedicated worker service
- Welcome-email background task simulation

## 6. Automated Testing

Pytest coverage includes:

- Authentication
- Registration/login
- Protected routes
- Admin RBAC
- Products
- Cart
- Checkout
- Inventory validation
- Atomic stock reservation
- Order cancellation
- Stock restoration
- Order lifecycle
- Shipping creation
- Shipping rollback
- Shipping admin RBAC
- Shipping lifecycle timestamps
- Payment persistence
- Duplicate payment protection
- Payment ownership protection
- End-to-end purchase flow

Latest full suite:

```text
30 passed
```

## 7. Database

Current application tables:

```text
users
categories
products
cart_items
orders
order_items
shipping
payments
alembic_version
```

Alembic is the authoritative schema-management mechanism.

Current migration chain relevant to the latest domain additions:

```text
40f98fd888bb_add_shipping_table.py
                |
                v
cff58edd10a9_add_payments_table.py
                |
                v
              HEAD
```

## 8. Technology Stack

- Python 3.12 slim
- FastAPI 0.104.1
- Uvicorn
- PostgreSQL 15 Alpine
- SQLAlchemy 2.x
- Redis 7 Alpine
- JWT
- Alembic 1.13.1
- Docker / Docker Compose
- Pytest / HTTPX
- SlowAPI
- Celery 5.3.6
- Swagger / OpenAPI
- GitHub Actions

## 9. Repository Status

Documentation on GitHub has been updated for Step 30.

The application implementation for Step 30 consists of:

```text
alembic/env.py
app/modules/order/models.py
app/modules/payment/models.py
app/modules/payment/router.py
tests/test_shop.py
alembic/versions/cff58edd10a9_add_payments_table.py
```

Before declaring the repository milestone fully synchronized, confirm that the local Step 30 implementation has been committed and pushed and that GitHub Actions is green.

## 10. Major Lessons Learned

- Redis is shared by product caching, rate limiting, and Celery.
- Alembic is the authoritative schema-management mechanism.
- Inventory must be re-checked during checkout even after cart validation.
- Checkout and stock changes must remain in one transaction.
- Row-level locking is required for concurrent inventory updates.
- Cancellation must restore reserved inventory safely.
- Cancellation must be restricted to valid order states.
- Order ownership must be checked before allowing cancellation.
- Stock restoration should use row-level locking for consistency with checkout.
- A payment should be persisted as a domain entity rather than represented only by a response.
- `order_id` being unique enforces the one-payment-per-order rule at the database level.
- `transaction_id` must be unique to avoid duplicate transaction identifiers.
- The current payment gateway is intentionally a mock; real gateway/refund integration is future work.

## 11. Current Known Good State

```text
Step 25 — Shipping and Delivery Management     COMPLETED
Step 30 — Persistent Payment Records            IMPLEMENTED
Tests                                            30 passed
Alembic head                                    cff58edd10a9
```

## 12. Pending Work

- Synchronize Step 30 implementation with GitHub if local changes are still unpushed.
- Confirm green CI for the Step 30 commit.
- Continue with the next planned development step only after repository synchronization.

## 13. Future Enhancements

- Real payment gateway integration
- Real refund workflow
- Payment provider webhooks
- Idempotency keys for payment requests
- Payment audit history
- Real email provider
- Refresh tokens
- Structured logging
- Metrics and monitoring
- Distributed tracing
- Production configuration
- Security hardening
- API versioning
- Inventory audit history
- Advanced reservation/release policies
- Celery retry policies and monitoring

## 14. Next Recommended Step

After Step 30 is committed, pushed, and verified by green GitHub Actions, continue to the next planned development milestone.

Do not start the next feature while the current implementation, tests, documentation, Git state, and CI status are inconsistent.

## 15. Notes For Future Sessions

Always begin by checking:

```bash
git status --short
git log -1 --oneline
docker compose exec web pytest -q
docker compose exec web alembic current
```

Then compare the local state with `PROJECT_STATE.md` and the latest GitHub state before making changes.
