# PROJECT_STATE

## 1. Objective

Build a production-oriented e-commerce backend using FastAPI, PostgreSQL, Redis, SQLAlchemy, JWT authentication, Alembic, Docker, automated testing, CI/CD, caching, rate limiting, background task processing, inventory management, and production-readiness practices.

The project is developed incrementally. Every completed step must be tested, documented, committed, and pushed to GitHub before moving to the next step.

---

## 2. Current Project Status

### Completed Steps

- Step 1 — Project setup and initial inspection
- Step 2 — Configuration and security
- Step 3 — User module
- Step 4 — PostgreSQL and authentication
- Step 5 — Alembic database migrations
- Step 6 — Dockerization and Docker Compose
- Step 7 — JWT protected routes
- Step 8 — RBAC / Admin authorization
- Step 9 — Product and Category catalog
- Step 10 — Product catalog search, pagination, and category filtering
- Step 11 — Shopping cart
- Step 12 — Order checkout and order history
- Step 13 — Mock payment processing
- Step 14 — Pytest automated testing framework
- Step 15 — End-to-end shopping flow tests
- Step 16 — GitHub Actions CI
- Step 17 — Alembic as the application's database schema management system
- Step 18 — Redis caching for the product catalog
- Step 19 — Redis-backed rate limiting
- Step 20 — Celery background worker
- Step 21 — Alembic schema reconciliation and migration-aware CI
- Step 22 — Inventory management and atomic stock reservation
- Step 23 — Order cancellation and stock restoration
- Step 24 — Order lifecycle and admin order management
- Step 25 — Shipping and delivery management

### Current Step

Step 25 is the latest completed and verified development step.

Order lifecycle management is centralized with explicit status-transition rules. Admin users can update order status through a protected endpoint, while invalid transitions and non-admin access are rejected. Shipping and delivery management are now attached to each order and integrated with checkout and lifecycle transitions.

The valid lifecycle is:

```text
pending → paid → processing → shipped → delivered
   │
   └────────────→ cancelled
```

Order cancellation remains limited to `pending` orders and restores reserved stock using row-level locking.

Latest verified full test result:

```text
24 passed
```

---

## 3. Current Architecture

```text
Client / Frontend
       |
       v
    FastAPI (web)
       |
       +---- User Module
       |       +---- Registration
       |       +---- Login
       |       +---- JWT authentication
       |       +---- Current user
       |       +---- Admin authorization
       |
       +---- Product Module
       |       +---- Categories
       |       +---- Products
       |       +---- Search
       |       +---- Pagination
       |       +---- Category filtering
       |       +---- Inventory / stock quantity
       |       +---- Redis caching
       |
       +---- Cart Module
       |       +---- User-specific cart
       |       +---- Add / increment
       |       +---- Stock validation
       |       +---- View
       |       +---- Remove
       |
       +---- Order Module
       |       +---- Checkout
       |       +---- Cancellation
       |       +---- Lifecycle management
       |       +---- Admin status management
       |       +---- Shipping integration
       |       +---- Order items
       |       +---- Price locking
       |       +---- Atomic stock reservation
       |       +---- Stock restoration on cancellation
       |       +---- Order history
       |
       +---- Shipping Module
       |       +---- Shipping address
       |       +---- Carrier / tracking number
       |       +---- shipped_at / delivered_at
       |       +---- Admin shipping management
       |
       +---- Payment Module
       |       +---- Mock payment processing
       |       +---- Transaction ID generation
       |
       +---- Rate Limiting
       |       +---- SlowAPI
       |       +---- Redis storage
       |
       +---- Background Tasks
               +---- Celery
               +---- Welcome-email task

                 |                 |
                 v                 v
             PostgreSQL          Redis
                 |                 |
                 +-----------------+

Docker Compose services:

    db ------------- PostgreSQL
    redis ---------- Redis
    web ------------ FastAPI
    celery_worker -- Celery Worker
```

---

## 4. Technology Stack

- Python 3.12 slim Docker base image
- FastAPI 0.104.1
- Uvicorn
- PostgreSQL 15 Alpine
- SQLAlchemy 2.x
- Redis 7 Alpine
- Redis Python client
- JWT authentication
- Alembic 1.13.1
- Docker
- Docker Compose
- Pytest
- HTTPX
- SlowAPI
- Celery 5.3.6
- Swagger / OpenAPI
- GitHub Actions

---

## 5. Implemented Features

### 5.1 Application

- FastAPI application
- Uvicorn development server
- Environment-based configuration
- Swagger / OpenAPI documentation
- Health endpoint
- SQLAlchemy database session management
- Dockerized application

### 5.2 User Management

- User registration
- Duplicate email detection
- Password hashing
- User login
- JWT access token generation
- Invalid credential handling
- Current authenticated user endpoint
- `is_superuser` support

### 5.3 Authentication and Authorization

- JWT Bearer authentication
- `get_current_user` dependency
- Protected routes
- OAuth2 password form compatibility using `python-multipart`
- `get_current_admin_user` dependency
- Admin-only protected endpoints
- Regular users receive HTTP 403 on admin-only endpoints
- Superusers receive HTTP 200 on admin-only endpoints

### 5.4 Product Catalog

Product fields:

- `id`
- `title`
- `description`
- `price`
- `stock_quantity`
- `is_active`
- `category_id`

Catalog endpoints:

- `GET /categories/`
- `POST /categories/` — admin only
- `GET /products/`
- `POST /products/` — admin only

Product listing supports:

- `skip` / `limit` pagination
- `search` filtering by title
- Case-insensitive title search using SQLAlchemy `ilike`
- `category_id` filtering
- Redis caching
- Cache invalidation after product creation

### 5.5 Shopping Cart

- `CartItem` SQLAlchemy model
- User-specific cart isolation
- `GET /cart/`
- `POST /cart/`
- `DELETE /cart/{item_id}`
- JWT protection
- Stock validation when adding a product
- Stock validation when incrementing an existing cart item
- HTTP 400 with `Insufficient stock` when requested quantity exceeds stock

### 5.6 Orders

- `Order` SQLAlchemy model
- `OrderItem` SQLAlchemy model
- Checkout flow
- `POST /orders/checkout`
- `GET /orders/`
- Order total calculation
- Unit-price locking
- Cart cleanup after successful checkout
- User order history

#### Inventory Reservation During Checkout

Checkout uses row-level locking with SQLAlchemy `with_for_update()`.

The checkout transaction:

1. Retrieves the user's cart.
2. Locks each required product row.
3. Verifies sufficient stock.
4. Decrements `stock_quantity`.
5. Creates order items.
6. Creates the order.
7. Clears the cart.
8. Commits the transaction.

If stock is insufficient, checkout returns HTTP 400 and the transaction is rolled back.

#### Order Cancellation and Stock Restoration

Step 23 adds:

- `POST /orders/{order_id}/cancel`
- Order ownership validation
- Cancellation allowed only while status is `pending`
- Product row locking with `with_for_update()` during stock restoration
- Restoration of `OrderItem.quantity` back to `Product.stock_quantity`
- Order status transition `pending → cancelled`
- Transactional update of stock and order status
- Rejection of cancellation for `paid` or already-cancelled orders
- HTTP 404 for orders that do not belong to the current user

#### Order Lifecycle and Admin Management

Step 24 adds centralized lifecycle rules for order status transitions:

- `pending → paid`
- `pending → cancelled`
- `paid → processing`
- `processing → shipped`
- `shipped → delivered`

Terminal states are `delivered` and `cancelled`. Invalid transitions return HTTP 400.

Admin status endpoint:

- `PATCH /orders/{order_id}/status`
- Requires `get_current_admin_user`
- Validates the requested transition against `ALLOWED_STATUS_TRANSITIONS`
- Returns HTTP 404 for unknown orders
- Returns HTTP 403 for regular users

#### Shipping and Delivery Management

Step 25 adds a dedicated `Shipping` entity with a one-to-one relationship to `Order`.

Implemented features:

- `Shipping` model and Alembic migration `40f98fd888bb`
- Shipping address, city, and postal code captured during checkout
- Shipping information included in `OrderResponse`
- `PATCH /shipping/{order_id}` for admin carrier and tracking updates
- Admin-only shipping updates
- `shipped_at` recorded when an order transitions to `shipped`
- `delivered_at` recorded when an order transitions to `delivered`
- Transactional checkout creation of Order + Shipping
- Rollback coverage ensuring failed checkout does not create an Order or Shipping record
- Order/Shipping bidirectional one-to-one relationship

Current shipping fields:

```text
address
city
postal_code
carrier
tracking_number
shipped_at
delivered_at
```

### 5.7 Mock Payment

- `POST /payment/process`
- Pending-order validation
- Successful payment changes order status to `paid`
- UUID transaction ID generation
- Prevention of duplicate payment processing

### 5.8 Automated Testing

Pytest coverage includes:

- Authentication
- Registration
- Login
- Protected routes
- Admin authorization
- Product operations
- Cart operations
- Checkout
- Payment
- Inventory validation
- Stock reduction
- Order cancellation
- Stock restoration after cancellation
- Invalid cancellation states
- Order ownership validation
- Admin order lifecycle transitions
- Invalid order status transitions
- Regular-user RBAC for order status updates
- Unknown-order handling for admin status updates
- Shipping creation during checkout
- Shipping rollback on failed checkout
- Admin shipping management
- Regular-user shipping RBAC
- Shipping lifecycle timestamps
- Unknown-shipping handling
- End-to-end shopping flow

Latest full test result:

```text
24 passed
```

Verification command:

```bash
docker compose exec web pytest -q
```

### 5.9 CI/CD

Workflow:

```text
.github/workflows/ci.yml
```

The workflow:

- Checks out the repository
- Creates `.env` from GitHub Secrets
- Builds and starts Docker Compose
- Waits for PostgreSQL
- Runs `alembic upgrade head`
- Runs Pytest

CI triggers on pushes and pull requests targeting `main`.

### 5.10 Database Migrations

Alembic is the application's database schema management system.

Migrations include:

```text
aee86fd59c30
b8c2d1e4f6a7
3105be9533db_add_product_stock_quantity.py
40f98fd888bb_add_shipping_table.py
```

The inventory migration adds `products.stock_quantity`.

Step 25 adds the `shipping` table through Alembic migration `40f98fd888bb_add_shipping_table.py`.

### 5.11 Redis Caching

- Redis 7 Docker service
- Product catalog caching
- Dynamic cache keys
- Pagination-aware caching
- Search-aware caching
- Category-aware caching
- Cache invalidation after product creation

### 5.12 Inventory Management

- Product-level `stock_quantity`
- Cart-level stock validation
- Atomic checkout stock decrement
- Row-level locking during checkout
- Transaction rollback on insufficient stock
- Stock restoration when a pending order is cancelled
- Row-level locking during stock restoration

### 5.13 Rate Limiting

SlowAPI uses Redis as the storage backend.

Login limit:

```text
5 requests per minute
```

### 5.14 Celery Background Processing

- Celery 5.3.6
- Redis broker
- Redis result backend
- JSON serialization
- UTC configuration
- Dedicated `celery_worker` service
- `send_welcome_email_task`
- Asynchronous task dispatch after registration

The welcome-email task is still a simulation and does not send real email.

---

## 6. Database

PostgreSQL is the primary relational database.

Current known tables:

```text
users
categories
products
cart_items
orders
order_items
shipping
alembic_version
```

SQLAlchemy is the ORM.

Alembic manages schema changes.

The application does not use direct `create_all()` as its migration strategy.

---

## 7. Docker

Current Docker Compose services:

```text
db
redis
web
celery_worker
```

### db

- PostgreSQL 15 Alpine
- Persistent volume
- Internal network
- Host port exposure disabled

### redis

- Redis 7 Alpine
- Internal network
- Host port 6379 currently mapped
- Used by caching, rate limiting, and Celery

### web

- Project Docker image
- FastAPI + Uvicorn
- Port 8000
- `.env`
- Depends on PostgreSQL and Redis

### celery_worker

- Same project image
- Celery worker
- Depends on Redis and PostgreSQL
- Shares the internal network

---

## 8. Current Known Good State

### Step 20 — Celery Background Worker

Status: **Completed and verified**

### Step 21 — Alembic Schema Reconciliation and Migration-Aware CI

- Fresh environments receive the schema required by current models.
- Historical databases remain compatible with the reconciliation migration.
- CI applies `alembic upgrade head` before tests.

Status: **Completed and verified**

### Step 22 — Inventory Management and Atomic Stock Reservation

- Added `Product.stock_quantity`.
- Added stock validation in cart operations.
- Added atomic stock decrement during checkout.
- Added row-level locking during checkout.
- Added inventory tests.

Latest Step 22 verification:

```text
10 passed
```

Status: **Completed and verified**

### Step 23 — Order Cancellation and Stock Restoration

Implemented:

- `POST /orders/{order_id}/cancel`
- Current-user ownership validation
- Pending-only cancellation
- Product row locking with `with_for_update()`
- Stock restoration from order items
- `pending → cancelled` status transition
- Rejection of already-cancelled orders
- Rejection of paid orders
- Rejection of orders belonging to another user
- Automated tests for cancellation and stock restoration

Latest Step 23 verification:

```text
8 shop tests passed
14 full-project tests passed
```

Status: **Completed and verified**

### Step 24 — Order Lifecycle and Admin Order Management

Implemented:

- Centralized `ALLOWED_STATUS_TRANSITIONS` rules
- Valid lifecycle: `pending → paid → processing → shipped → delivered`
- Cancellation branch: `pending → cancelled`
- Terminal `delivered` and `cancelled` states
- `PATCH /orders/{order_id}/status` admin endpoint
- Admin authorization through `get_current_admin_user`
- Rejection of invalid status transitions with HTTP 400
- Rejection of regular-user status changes with HTTP 403
- Unknown-order handling with HTTP 404
- Admin test fixture for authenticated status-management tests
- Automated lifecycle and RBAC test coverage

Latest Step 24 verification:

```text
18 passed
```

Status: **Completed and verified**

### Step 25 — Shipping and Delivery Management

Implemented:

- Dedicated `Shipping` model
- One-to-one `Order` ↔ `Shipping` relationship
- Alembic migration `40f98fd888bb_add_shipping_table.py`
- Shipping address captured during checkout
- Shipping data exposed through `OrderResponse`
- `PATCH /shipping/{order_id}` admin endpoint
- Carrier and tracking-number management
- `shipped_at` timestamp on `processing → shipped`
- `delivered_at` timestamp on `shipped → delivered`
- Transactional Shipping creation during checkout
- Failed-checkout rollback coverage
- Admin and regular-user shipping authorization tests

Latest Step 25 verification:

```text
24 passed
```

Status: **Completed and verified**

---

## 9. Major Lessons Learned

- Redis is shared by product caching, rate limiting, and Celery.
- Alembic is the authoritative schema-management mechanism.
- Inventory must be re-checked during checkout even after cart validation.
- Checkout and stock changes must remain in one transaction.
- Row-level locking is required for concurrent inventory updates.
- Cancellation must restore reserved inventory safely.
- Cancellation must be restricted to valid order states.
- Order ownership must be checked before allowing cancellation.
- Stock restoration should use row-level locking for consistency with checkout.
- The current payment implementation is a mock and does not include real refunds.
- Because real payment/refund integration is not implemented yet, paid orders are not cancellable.
- Order status transitions should be centralized rather than duplicated across endpoints.
- Admin-only lifecycle changes should use the existing RBAC dependency.
- Shipping belongs to the order as a one-to-one domain object.
- Checkout should create order and shipping information atomically.
- Shipping timestamps should be tied to lifecycle transitions rather than manually inferred from API calls.
- Shipping updates should remain admin-only.

---

## 10. Repository Status

Repository:

```text
maherani/ecommerce_backend
```

Branch:

```text
main
```

Latest completed remote development milestone:

```text
Step 25 — Shipping and Delivery Management
```

Latest verified test result:

```text
24 passed
```

Step 25 is committed and pushed to GitHub. GitHub Actions is green for the Step 25 changes.

Recent Step 25 commits:

```text
32b6f63540a96e83988f45357aefef42545fe4a5
feat: add shipping and delivery management

bb1b024d87e34aa953834240b709b97b565a00cb
fix: link order and shipping models

a84608d0df52c159ed2c07a69c4845928d5a9eeb
fix: correct shipping rollback test
```

Current modified project areas introduced by Step 25:

```text
alembic/env.py
alembic/versions/40f98fd888bb_add_shipping_table.py
app/modules/order/models.py
app/modules/order/router.py
app/modules/order/schemas.py
app/modules/shipping/models.py
app/modules/shipping/router.py
app/modules/shipping/schemas.py
main.py
tests/test_shop.py
```

---

## 11. Important Project Files

```text
PROJECT_STATE.md
README.md
Dockerfile
docker-compose.yml
requirements.txt
alembic.ini
alembic/
app/
tests/
.github/workflows/ci.yml
```

Important business modules:

```text
app/modules/user/
app/modules/product/
app/modules/cart/
app/modules/order/
app/modules/payment/
app/modules/shipping/
```

Important tests:

```text
tests/conftest.py
tests/test_shop.py
```

`PROJECT_STATE.md` is the primary project-memory document and must remain synchronized with the actual repository state.

---

## 12. Pending Work

### Immediate

- Review the current payment flow before starting the next feature.
- Decide whether Step 26 should introduce real payment/refund behavior or another high-value domain capability based on the repository state.
- Keep `PROJECT_STATE.md` and `README.md` synchronized with GitHub after each completed step.

### Planned Features

- Real payment gateway and refund integration
- Administration expansion
- Real email delivery integration
- Structured logging
- Monitoring and observability
- Metrics
- Distributed tracing
- Production hardening
- Production configuration
- Security hardening
- API versioning
- Expanded automated test coverage
- Advanced inventory reservation and release policies
- Celery retry policies and task monitoring
- Additional background workflows

---

## 13. Future Enhancements

- Stronger password validation
- Refresh tokens
- Real payment gateway integration
- Real refund workflow
- Real email provider integration
- Inventory reservation expiration
- Stock restoration after additional order states
- Inventory audit history
- Administration inventory endpoints
- Structured logging
- Monitoring
- Metrics
- Distributed tracing
- Production configuration
- Security hardening
- API versioning
- Expanded automated test coverage

---

## 14. Next Recommended Step

Before starting Step 26:

1. Review the current payment implementation and its relationship to the order lifecycle and shipping flow.
2. Select the next feature based on the actual repository state.
3. Define tests before implementation.
4. Update documentation as part of the step.
5. Verify the full test suite and CI before closing the step.

Do not start the next feature blindly.

---

## 15. Development Rules

1. No step is complete without successful tests.
2. Do not move to the next step before the current step is tested.
3. Documentation must be updated during development.
4. Use one recommended solution instead of unnecessary alternatives.
5. Add useful comments to new or modified code.
6. Commit and push after every completed step.
7. Keep `PROJECT_STATE.md` synchronized with the real project state.
8. Inspect existing code before modifying it.
9. Do not remove data or functionality without verifying its purpose and impact.
10. Review Git changes before committing.
11. Review documentation before every push.
12. Use Alembic for database schema changes.
13. Verify inventory and order-state transitions with automated tests.
14. Keep documentation chronological and consistent with the repository.
15. Verify CI after each completed development step.
