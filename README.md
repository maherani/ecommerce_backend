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
- SQLAlchemy
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
       +---- Cart
       +---- Orders / Checkout
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

Products are associated with categories using a foreign key.

The product listing supports:

- `skip` / `limit` pagination
- `search` filtering by product title
- Case-insensitive title search using SQLAlchemy `ilike`
- `category_id` filtering
- Redis caching based on the list-query parameters
- Cache invalidation after product creation

### Shopping Cart

- User-specific cart
- Add / increment product quantity
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
- Cart cleared after successful checkout
- Order history

Main endpoints:

```text
POST /orders/checkout
GET  /orders/
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

The test suite covers areas including:

- Authentication
- Registration
- Login
- Protected routes
- Admin authorization
- Products
- Categories
- Cart
- Orders
- Payment
- End-to-end shopping flow
- Security-related behavior

Run the test suite inside the Docker application container:

```bash
docker compose exec web pytest
```

A development step is not considered complete until its relevant tests succeed.

## CI/CD

GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

The workflow builds the Docker environment and runs the Pytest suite on push / pull-request activity targeting `main`.

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

A step is not complete until its test succeeds.

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

## Current Development Progress

```text
Step 1  — Project Setup                         ✅
Step 2  — Configuration & Security             ✅
Step 3  — User Module                          ✅
Step 4  — PostgreSQL & Authentication          ✅
Step 5  — Alembic                              ✅
Step 6  — Dockerization                        ✅
Step 7  — JWT Protected Routes                 ✅
Step 8  — RBAC / Admin Authorization           ✅
Step 9  — Product & Category Catalog           ✅
Step 10 — Product Search & Pagination          ✅
Step 11 — Shopping Cart                        ✅
Step 12 — Orders & Checkout                    ✅
Step 13 — Mock Payment                         ✅
Step 14 — Automated Testing                    ✅
Step 15 — E2E Shopping Flow                    ✅
Step 16 — GitHub Actions CI                   ✅
Step 17 — Alembic Schema Management            ✅
Step 18 — Redis Product Caching                ✅
Step 19 — Redis Rate Limiting                  ✅
Step 20 — Celery Background Worker             ✅
```

## Project Status

The latest completed development step is **Step 20 — Celery Background Worker**.

The current background task infrastructure is ready for further development, but the welcome-email implementation is still a simulation rather than a real email-provider integration.

## Future Roadmap

Planned areas include:

- Real email delivery integration
- Inventory management
- Shipping management
- Administration expansion
- Refresh tokens
- Real payment gateway integration
- Structured logging
- Monitoring
- Metrics
- Distributed tracing
- Production configuration
- Security hardening
- API versioning
- Expanded automated test coverage
- Celery retry policies and task monitoring
- Additional background workflows for email, order processing, and notifications

## Documentation

The primary project-state document is:

```text
PROJECT_STATE.md
```

It contains the detailed architecture, completed steps, known-good state, lessons learned, repository status, pending work, and rules required to continue the project in a future development session.
