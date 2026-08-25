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
- Atomic stock reservation during checkout
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
       |
       +---- Cart
       |        +---- User-specific cart
       |        +---- Stock validation
       |
       +---- Orders / Checkout
       |        +---- Cancellation
       |        +---- Order Lifecycle
       |        +---- Admin Status Management
       |        +---- Atomic Stock Reservation
       |        +---- Stock Restoration
       |
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

All services communicate through the internal:

```text
backend_network
```

PostgreSQL is not exposed directly to the host. Redis is used internally by the application and Celery stack.

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

Regular users receive HTTP 403 when accessing admin-only endpoints, while superusers are allowed to access them.

### Product Catalog

Categories:

```text
GET  /categories/
POST /categories/    # Admin
```

Products:

```text
GET  /products/
POST /products/      # Admin
```

Product fields currently include:

```text
id
title
description
price
stock_quantity
is_active
category_id
```

The product listing supports:

- `skip` / `limit` pagination
- `search` filtering by product title
- Case-insensitive title search using SQLAlchemy `ilike`
- `category_id` filtering
- Redis caching based on list-query parameters
- Cache invalidation after product creation

### Inventory Management

Inventory is tracked with:

```text
Product.stock_quantity
```

Current inventory rules:

- Users cannot add more units to their cart than the available stock.
- Increasing an existing cart quantity is validated against current stock.
- Checkout performs a final stock validation.
- Checkout locks product rows using SQLAlchemy `with_for_update()`.
- Stock is decremented inside the same database transaction as order creation.
- Insufficient stock causes checkout to fail with HTTP 400 and roll back the transaction.
- Pending-order cancellation restores the reserved quantity to product stock.
- Stock restoration uses row-level locking as well.

### Shopping Cart

- User-specific cart
- Add / increment product quantity
- Stock validation during add/increment
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

- Checkout from the current user's cart
- Order and order-item creation
- Total calculation
- Product price locked into order items
- Atomic stock decrement
- Row-level locking during checkout
- Cart cleared after successful checkout
- Order history

Main endpoints:

```text
POST /orders/checkout
GET  /orders/
```

### Order Lifecycle & Admin Management

The controlled order lifecycle is:

```text
pending → paid → processing → shipped → delivered
   │
   └────────────→ cancelled
```

Valid transitions are centralized in `ALLOWED_STATUS_TRANSITIONS`.

Valid transitions:

- `pending → paid`
- `pending → cancelled`
- `paid → processing`
- `processing → shipped`
- `shipped → delivered`

`delivered` and `cancelled` are terminal states.

Admin status endpoint:

```text
PATCH /orders/{order_id}/status
```

The endpoint:

- Requires `get_current_admin_user`
- Validates the requested transition
- Returns HTTP 400 for invalid transitions
- Returns HTTP 403 for regular users
- Returns HTTP 404 for unknown orders

### Order Cancellation & Stock Restoration

Pending orders can be cancelled using:

```text
POST /orders/{order_id}/cancel
```

Cancellation:

- Verifies order ownership
- Allows cancellation only for `pending` orders
- Locks the related product rows
- Restores `OrderItem.quantity` to `Product.stock_quantity`
- Changes status from `pending` to `cancelled`
- Commits stock restoration and status change transactionally

Paid orders are not cancellable because the current payment implementation does not provide a real refund workflow.

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

Cache keys include the relevant product-list parameters so different combinations of pagination, search, and category filtering do not incorrectly share cached responses.

Product creation invalidates the relevant catalog cache.

### Rate Limiting

SlowAPI is integrated with Redis for rate-limit storage.

The login endpoint currently uses:

```text
5 requests / minute
```

This protects the login endpoint against repeated brute-force attempts.

### Celery Background Tasks

Celery is integrated with Redis as both broker and result backend.

Current infrastructure includes:

- `app/core/celery_app.py`
- `app/tasks/email_tasks.py`
- Dedicated `celery_worker` Docker Compose service
- JSON task serialization
- UTC configuration
- `send_welcome_email_task`
- Successful user registration queues the task asynchronously

The current welcome-email task intentionally simulates a slow email operation and logs a successful result. It does **not** send a real email yet.

## Database

PostgreSQL is the primary relational database.

Current database tables:

```text
users
categories
products
cart_items
orders
order_items
alembic_version
```

SQLAlchemy is used as the ORM.

Alembic is used for database schema migrations.

Direct `create_all` schema management is no longer the application's migration strategy; schema changes are managed through Alembic migrations.

The inventory migration adds `products.stock_quantity`.

No new database migration was required for Step 23 or Step 24 because cancellation and lifecycle management use the existing order and product tables.

## API

Main endpoints currently include:

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
PATCH  /orders/{order_id}/status

POST   /payment/process
```

Protected endpoints require a valid JWT Bearer token.

Admin endpoints require a superuser account.

## Swagger / OpenAPI

After starting the application:

```text
http://127.0.0.1:8000/docs
```

Swagger is the primary tool used for manual API verification during development.

## Running the Project

### 1. Activate the virtual environment

```bash
source venv/bin/activate
```

### 2. Start Docker Compose

```bash
docker compose up -d
```

This starts:

- FastAPI
- PostgreSQL
- Redis
- Celery Worker

### 3. Check containers

```bash
docker compose ps
```

### 4. Open Swagger

```text
http://127.0.0.1:8000/docs
```

### 5. Check Celery worker logs

```bash
docker compose logs -f celery_worker
```

## Database Migrations

Check the current Alembic revision:

```bash
alembic current
```

Check available migration heads:

```bash
alembic heads
```

Apply migrations:

```bash
alembic upgrade head
```

Create a migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe change"
```

Always review generated migrations before applying them.

## Testing

The project uses Pytest and HTTPX for automated API testing.

The test suite covers:

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
- Order lifecycle transitions
- Invalid status transitions
- Admin RBAC for status updates
- Payment
- End-to-end shopping flow
- Welcome-email task dispatch

Run the test suite inside the Docker application container:

```bash
docker compose exec web pytest
```

The latest local verification for Step 24 is:

```text
18 passed
```

A development step is not considered complete until its relevant tests succeed.

## CI/CD

GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

The workflow builds the Docker environment, waits for PostgreSQL, applies `alembic upgrade head`, and runs the Pytest suite on push / pull-request activity targeting `main`.

## Development Workflow

Every development step follows:

```text
Inspect
   ↓
Explain the reason
   ↓
Implement
   ↓
Test
   ↓
Update documentation
   ↓
Review Git changes
   ↓
Commit
   ↓
Push
   ↓
Next step
```

A step is not complete until its test succeeds and the repository state has been reviewed.

## Project Development Rules

1. Do not move to the next step before the current step is tested.
2. Documentation must be updated during development.
3. Use one recommended solution instead of presenting unnecessary alternatives.
4. Add useful comments to new or modified code.
5. Commit and push after every completed step.
6. Keep `PROJECT_STATE.md` synchronized with the real project state.
7. Explain the reason for installations, files, tools, configuration changes, and code changes.
8. Inspect existing code before modifying it.
9. Do not remove existing functionality or data without checking its purpose and impact.
10. Keep project state documented so development can continue in a new chat.
11. Review `git diff --check` and `git status` before committing.
12. Verify relevant tests before marking a development step complete.
13. Update both `README.md` and `PROJECT_STATE.md` when a development step changes the architecture or implemented features.

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
Step 24 — Order Lifecycle & Admin Management    🟡
```

## Project Status

The current development step is:

```text
Step 24 — Order Lifecycle and Admin Order Management
```

Step 24 has been implemented and verified locally, but the code changes are still pending commit and push.

The system now has a controlled order lifecycle, admin-only status management, validated status transitions, order cancellation, and inventory restoration.

The current test suite passes with:

```text
18 passed
```

The real payment/refund workflow is still not implemented. Paid orders therefore remain non-cancellable until refund handling exists.

## Order Lifecycle and Admin Management

Current lifecycle:

```text
pending → paid → processing → shipped → delivered
   │
   └────────────→ cancelled
```

Admin-only status updates are handled by `PATCH /orders/{order_id}/status`. The transition rules are centralized in `ALLOWED_STATUS_TRANSITIONS`.

Implemented Step 24 protections:

- Invalid transitions return HTTP 400.
- Regular users cannot change order status.
- Unknown orders return HTTP 404.
- `delivered` and `cancelled` are terminal states.

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

The primary project-state document is:

```text
PROJECT_STATE.md
```

It contains the architecture, completed steps, current known-good state, lessons learned, repository status, pending work, future enhancements, and development rules required to continue the project in a future session.
