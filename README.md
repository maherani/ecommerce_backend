# E-Commerce Backend

Production-oriented e-commerce backend built with **FastAPI, PostgreSQL, Redis, SQLAlchemy, JWT authentication, Alembic, Docker, Pytest, GitHub Actions, SlowAPI, and Celery**.

The project is developed incrementally. Every completed step is tested, documented, committed, and pushed to GitHub before the next step begins.

## Project Objective

Build a maintainable, secure, testable, and production-oriented backend for an e-commerce platform.

The project focuses on:

- Clean architecture
- Authentication and authorization
- Database migrations
- Containerization
- Automated testing
- Search and pagination
- Shopping cart and checkout
- Inventory and stock management
- Atomic stock reservation
- Order cancellation and stock restoration
- Payment workflow simulation
- Redis caching
- Rate limiting
- Background task processing
- CI/CD
- Documentation
- Security
- Observability and production readiness

## Technology Stack

- Python 3.12
- FastAPI
- Uvicorn
- PostgreSQL 15
- SQLAlchemy 2.x
- Redis 7
- JWT Authentication
- Alembic
- Docker
- Docker Compose
- Pytest
- HTTPX
- SlowAPI
- Celery 5.3.6
- Swagger / OpenAPI
- GitHub Actions

## Current Architecture

```text
Client / Frontend
       |
       v
    FastAPI (web)
       |
       +---- Users / Authentication / JWT
       +---- RBAC / Admin Authorization
       +---- Categories / Products
       |        +---- Search
       |        +---- Pagination
       |        +---- Category Filtering
       |        +---- Redis Cache
       |        +---- Inventory / Stock
       +---- Shopping Cart
       |        +---- Stock Validation
       +---- Orders / Checkout
       |        +---- Atomic Stock Reservation
       |        +---- Order Cancellation
       |        +---- Stock Restoration
       +---- Mock Payment
       +---- Rate Limiting
       +---- Background Tasks
                |
                v
          Celery Worker

       |                    |
       v                    v
   PostgreSQL             Redis
                            |
                            +---- Product Cache
                            +---- Rate Limit Storage
                            +---- Celery Broker / Result Backend
```

## Docker Architecture

```text
Docker Compose
│
├── web
│    └── FastAPI + Uvicorn
│
├── db
│    └── PostgreSQL 15
│
├── redis
│    └── Redis 7
│
└── celery_worker
     └── Celery Worker
```

All services communicate through the internal `backend_network`.

PostgreSQL is not exposed directly to the host.

## Current Features

### User Authentication

- User registration
- Duplicate email detection
- Password hashing
- User login
- JWT access tokens
- Invalid credential handling
- JWT Bearer authentication
- Current authenticated user
- Protected routes

### Authorization / RBAC

Role-based authorization is implemented using the `is_superuser` field.

Admin-only routes use:

```text
get_current_admin_user
```

Regular users receive HTTP 403 on admin-only endpoints, while superusers are allowed to access them.

### Product Catalog

Products support:

- Category association
- Search
- Pagination
- Category filtering
- Redis caching
- Inventory tracking through `stock_quantity`

Main endpoints:

```text
GET  /categories/
POST /categories/    # Admin
GET  /products/
POST /products/      # Admin
```

Current product fields:

```text
id
title
description
price
stock_quantity
is_active
category_id
```

### Inventory Management

Inventory is tracked with:

```text
stock_quantity
```

The current rules are:

- Products cannot be added to the cart beyond available stock.
- Increasing an existing cart item is also checked against current stock.
- Checkout re-checks stock before creating the order.
- Checkout locks product rows using SQLAlchemy `with_for_update()`.
- Stock is decremented inside the same transaction as order creation.
- Insufficient stock causes checkout to fail and the transaction to roll back.

### Shopping Cart

- User-specific cart
- Add / increment product quantity
- Stock validation
- Retrieve current cart
- Remove cart items
- JWT-protected cart operations

Main endpoints:

```text
GET    /cart/
POST   /cart/
DELETE /cart/{item_id}
```

### Orders / Checkout

- Checkout from current cart
- Order and order-item creation
- Total calculation
- Product price locking
- Atomic stock reservation
- Order history
- Order cancellation for pending orders
- Stock restoration after cancellation

Main endpoints:

```text
POST /orders/checkout
GET  /orders/
POST /orders/{order_id}/cancel
```

### Order Cancellation — Step 23

Step 23 adds:

```text
POST /orders/{order_id}/cancel
```

Cancellation behavior:

- The order must belong to the current authenticated user.
- Only `pending` orders can be cancelled.
- `paid` orders are rejected because real payment/refund handling is not implemented yet.
- Already-cancelled orders are rejected.
- Each product row is locked with `with_for_update()` before stock restoration.
- `OrderItem.quantity` is added back to `Product.stock_quantity`.
- The order status changes from `pending` to `cancelled`.
- Stock restoration and status update are committed as one transaction.

Example state transition:

```text
pending
   |
   | cancel
   v
cancelled
```

Stock flow:

```text
Checkout
   ↓
stock_quantity decreases
   ↓
Order = pending
   ↓
Cancel order
   ↓
stock_quantity restored
   ↓
Order = cancelled
```

### Mock Payment

- Payment processing endpoint
- Pending-order validation
- Order status changes to `paid` after successful payment
- UUID transaction ID generation
- Prevention of duplicate payment processing

Main endpoint:

```text
POST /payment/process
```

### Redis Caching

Redis is used for product catalog caching.

Cache keys include pagination, search, and category-filter parameters.

Product creation invalidates the relevant catalog cache.

Redis is also used for rate limiting and Celery.

### Rate Limiting

SlowAPI uses Redis for rate-limit storage.

The login endpoint currently uses:

```text
5 requests / minute
```

### Celery Background Tasks

Celery uses Redis as broker and result backend.

Current infrastructure:

```text
app/core/celery_app.py
app/tasks/email_tasks.py
celery_worker
```

Current task:

```text
send_welcome_email_task
```

The welcome-email task is still a simulation and does not send real email.

## Database

PostgreSQL is the primary relational database.

Current tables:

```text
users
categories
products
cart_items
orders
order_items
alembic_version
```

Alembic is the application's schema-management system.

The inventory migration is:

```text
3105be9533db_add_product_stock_quantity.py
```

Step 23 does not require a new database migration because it uses the existing order, order-item, and product columns.

## API

```text
GET    /

POST   /users/
POST   /users/login
GET    /users/me
GET    /users/admin-only

GET    /categories/
POST   /categories/

GET    /products/
POST   /products/

GET    /cart/
POST   /cart/
DELETE /cart/{item_id}

POST   /orders/checkout
GET    /orders/
POST   /orders/{order_id}/cancel

POST   /payment/process
```

Protected endpoints require a valid JWT Bearer token.

Admin endpoints require a superuser account.

## Swagger / OpenAPI

After starting the application:

```text
http://127.0.0.1:8000/docs
```

Swagger is the primary manual API verification tool used during development.

## Running the Project

### Activate the virtual environment

```bash
source venv/bin/activate
```

### Start Docker Compose

```bash
docker compose up -d
```

### Check containers

```bash
docker compose ps
```

### Run migrations

```bash
docker compose exec web alembic upgrade head
```

### Run tests

```bash
docker compose exec web pytest
```

### View Celery worker logs

```bash
docker compose logs -f celery_worker
```

## Database Migrations

Check current revision:

```bash
alembic current
```

Check heads:

```bash
alembic heads
```

Apply migrations:

```bash
alembic upgrade head
```

Create a migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

Always review generated migrations before applying them.

## Testing

The project uses Pytest and HTTPX.

Test coverage includes:

- Authentication
- Registration
- Login
- Protected routes
- Admin authorization
- Products
- Categories
- Cart
- Inventory validation
- Checkout
- Order cancellation
- Stock restoration
- Invalid order-state cancellation
- Order ownership checks
- Payment
- End-to-end shopping flow
- Welcome-email task dispatch

Run the full suite:

```bash
docker compose exec web pytest -q
```

Latest verified full-project result for Step 23:

```text
14 passed
```

Relevant cancellation tests verify:

```text
Pending order cancellation        ✅
Stock restoration                 ✅
Order status → cancelled          ✅
Repeated cancellation rejected    ✅
Paid order cancellation rejected  ✅
Other-user order rejected         ✅
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

A step is not complete until implementation, tests, documentation, Git review, commit, push, and CI verification are complete.

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
```

## Project Status

The latest development step is:

```text
Step 23 — Order Cancellation and Stock Restoration
```

The system can now restore reserved inventory when a pending order is cancelled.

The current order lifecycle is:

```text
Cart
  ↓
Checkout
  ↓
Pending Order + Reserved Stock
  ↓
 ┌───────────────┐
 │               │
 v               v
Payment       Cancellation
 ↓               ↓
Paid        Stock Restored
                 ↓
              Cancelled
```

The current project test suite passes with:

```text
14 passed
```

The real payment/refund workflow is still not implemented.

## Future Roadmap

Planned areas include:

- Real payment gateway integration
- Real refund workflow
- Real email provider integration
- Shipping management
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
- Inventory audit history
- Celery retry policies and task monitoring
- Additional background workflows

## Documentation

Primary project-state document:

```text
PROJECT_STATE.md
```

It contains the architecture, completed steps, known-good state, lessons learned, repository status, pending work, future enhancements, and development rules required to continue the project in a future session.
