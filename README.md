# E-Commerce Backend

Production-oriented e-commerce backend built with **FastAPI, PostgreSQL, Redis, SQLAlchemy, JWT authentication, Alembic, Docker, Pytest, GitHub Actions, SlowAPI, and Celery**.

The project is developed incrementally. Every completed step is tested, documented, committed, and pushed to GitHub before the next step begins.

## Architecture

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
       +---- Shipping Module
       +---- Payment Module
       +---- Rate Limiting
       +---- Background Tasks

                 |                 |
                 v                 v
             PostgreSQL          Redis
```

Docker Compose services:

```text
db ------------- PostgreSQL
redis ---------- Redis
web ------------ FastAPI
celery_worker -- Celery Worker
```

## Technology Stack

- Python 3.12
- FastAPI 0.104.1
- Uvicorn
- PostgreSQL 15 Alpine
- SQLAlchemy 2.x
- Redis 7 Alpine
- JWT authentication
- Alembic 1.13.1
- Docker / Docker Compose
- Pytest / HTTPX
- SlowAPI
- Celery 5.3.6
- Swagger / OpenAPI
- GitHub Actions

## Core Features

### Authentication & Authorization

- User registration and login
- JWT Bearer authentication
- Protected routes
- Admin / superuser authorization through `get_current_admin_user`
- Regular users receive HTTP 403 on admin-only endpoints

### Product Catalog

- Categories and products
- Admin-only product/category creation
- Pagination
- Title search
- Category filtering
- Redis caching
- Cache invalidation after product creation

### Shopping Cart

- User-specific cart
- Add / increment / remove
- Stock validation
- `Insufficient stock` protection

### Orders

- Checkout
- Order history
- Order items
- Unit-price locking
- Atomic inventory reservation
- Order cancellation and stock restoration
- Controlled order lifecycle
- Admin-only status management

### Shipping & Delivery — Step 25

Step 25 introduces shipping as a first-class domain object connected one-to-one with each order.

Shipping fields:

```text
address
city
postal_code
carrier
tracking_number
shipped_at
delivered_at
```

Checkout now accepts shipping address data and creates the Order and Shipping records in the same transaction.

Admin endpoint:

```text
PATCH /shipping/{order_id}
```

This endpoint allows an authenticated admin to update `carrier` and `tracking_number`.

Order lifecycle integration automatically records timestamps:

```text
processing → shipped
      ↓
shipping.shipped_at = now()

shipped → delivered
      ↓
shipping.delivered_at = now()
```

A dedicated Alembic migration creates the `shipping` table:

```text
40f98fd888bb_add_shipping_table.py
```

The Order and Shipping SQLAlchemy models use a one-to-one relationship.

### Mock Payment

- `POST /payment/process`
- Pending-order validation
- Payment changes order status to `paid`
- Transaction ID generation
- Duplicate-payment protection

The payment implementation is still a mock and does not provide a real gateway or refund workflow.

## Testing

The project uses Pytest and HTTPX.

Coverage includes:

- Authentication and authorization
- Product and cart operations
- Checkout and inventory
- Order cancellation
- Order lifecycle transitions
- Admin RBAC
- Shipping creation during checkout
- Shipping rollback on failed checkout
- Admin shipping management
- Regular-user shipping RBAC
- Shipping lifecycle timestamps
- Unknown-shipping handling
- End-to-end shopping flow

Run the full suite:

```bash
docker compose exec web pytest -q
```

Latest verified full-project result:

```text
24 passed
```

## CI/CD

Workflow:

```text
.github/workflows/ci.yml
```

The workflow:

1. Checks out the repository.
2. Creates `.env` from GitHub Secrets.
3. Builds and starts Docker Compose.
4. Waits for PostgreSQL.
5. Runs `alembic upgrade head`.
6. Runs Pytest.

Triggers:

```text
push → main
pull_request → main
```

Every completed development step is considered complete only after implementation, tests, documentation, Git review, commit, push, and CI verification.

## Current Development Progress

```text
Step 1  — Project Setup                         ✅
Step 2  — Configuration & Security              ✅
Step 3  — User Module                           ✅
Step 4  — PostgreSQL & Authentication           ✅
Step 5  — Alembic                               ✅
Step 6  — Dockerization                         ✅
Step 7  — JWT Protected Routes                  ✅
Step 8  — RBAC / Admin Authorization            ✅
Step 9  — Product & Category Catalog            ✅
Step 10 — Product Search & Pagination           ✅
Step 11 — Shopping Cart                         ✅
Step 12 — Orders & Checkout                     ✅
Step 13 — Mock Payment                          ✅
Step 14 — Automated Testing                     ✅
Step 15 — E2E Shopping Flow                     ✅
Step 16 — GitHub Actions CI                     ✅
Step 17 — Alembic Schema Management             ✅
Step 18 — Redis Product Caching                 ✅
Step 19 — Redis Rate Limiting                   ✅
Step 20 — Celery Background Worker              ✅
Step 21 — Alembic Schema Reconciliation         ✅
Step 22 — Inventory & Atomic Stock Reservation  ✅
Step 23 — Order Cancellation & Stock Restoration ✅
Step 24 — Order Lifecycle & Admin Order Management ✅
Step 25 — Shipping & Delivery Management        ✅
```

## Order Lifecycle

```text
pending → paid → processing → shipped → delivered
   │
   └────────────→ cancelled
```

Invalid transitions are rejected. `delivered` and `cancelled` are terminal states.

Admin status endpoint:

```text
PATCH /orders/{order_id}/status
```

## Shipping Lifecycle

```text
Checkout
   ↓
Order + Shipping created
   ↓
processing
   ↓
shipped + shipped_at
   ↓
delivered + delivered_at
```

## Database

Current known application tables include:

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

Alembic is the authoritative database schema-management mechanism. Review generated migrations before applying them.

## Development Workflow

```text
Inspect
   ↓
Explain
   ↓
Implement
   ↓
Test
   ↓
Update documentation
   ↓
Review Git diff
   ↓
Commit
   ↓
Push
   ↓
Verify CI
   ↓
Next step
```

## Project Status

The latest completed milestone is:

```text
Step 25 — Shipping and Delivery Management
```

Step 25 is implemented, tested, committed, pushed, and verified with green GitHub Actions.

The current system now combines inventory reservation, order cancellation, a controlled order lifecycle, and first-class shipping/delivery management.

## Future Roadmap

Planned areas include:

- Real payment gateway integration
- Real refund workflow
- Real email provider integration
- Administration expansion
- Refresh tokens
- Structured logging
- Monitoring
- Metrics
- Distributed tracing
- Production configuration
- Security hardening
- API versioning
- Expanded automated test coverage
- Advanced inventory reservation and release policies
- Advanced order workflow and refund integration
- Inventory audit history
- Celery retry policies and task monitoring
- Additional background workflows

## Documentation

Primary project-state document:

```text
PROJECT_STATE.md
```

It contains the architecture, completed steps, known-good state, lessons learned, repository status, pending work, future enhancements, and development rules required to continue the project in a future session.
