# E-Commerce Backend

Production-oriented e-commerce backend built with **FastAPI, PostgreSQL, Redis, SQLAlchemy, JWT authentication, Alembic, Docker, Pytest, GitHub Actions, SlowAPI, and Celery**.

The project is developed incrementally. Every completed step is tested, documented, committed, and pushed to GitHub before the next step begins.

---

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
- Payment workflow simulation
- Redis caching
- Rate limiting
- Background task processing
- CI/CD
- Documentation
- Security
- Observability and production readiness

---

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

---

## Current Architecture


Client / Frontend
       |
       v
    FastAPI (web)
       |
       +---- Users / Authentication / JWT
       |
       +---- RBAC / Admin Authorization
       |
       +---- Categories / Products
       |        +---- Search
       |        +---- Pagination
       |        +---- Category Filtering
       |        +---- Redis Cache
       |        +---- Inventory / Stock
       |
       +---- Shopping Cart
       |        +---- User-specific cart
       |        +---- Stock validation
       |
       +---- Orders / Checkout
       |        +---- Price locking
       |        +---- Atomic stock reservation
       |
       +---- Mock Payment
       |
       +---- Rate Limiting
       |
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
                            +---- Celery Broker
                            +---- Celery Result Backend


## Docker Architecture
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

## All services communicate through the internal:

backend_network

PostgreSQL is not exposed directly to the host.

Redis is used internally by:

Product caching
Rate limiting
Celery broker
Celery result backend

## Current Features
User Authentication
   User registration
   Duplicate email detection
   Password hashing
   User login
   JWT access tokens
   Invalid credential handling
   JWT Bearer authentication
   Current authenticated user
   Protected routes

Authorization / RBAC
   Role-based authorization is implemented using the is_superuser field.
Admin-only routes use:
   get_current_admin_user
   Regular users receive HTTP 403 when accessing admin-only endpoints.
   Superusers are allowed to access admin-only endpoints.

## Product Catalog
   Categories
      GET  /categories/
      POST /categories/    # Admin
   Products
      GET  /products/
      POST /products/      # Admin
   Products are associated with categories using a foreign key.

   The product listing supports:
      skip / limit pagination
      search filtering by product title
      Case-insensitive title search using SQLAlchemy ilike
      category_id filtering
      Redis caching based on list-query parameters
      Cache invalidation after product creation

## Product Model
   The product model currently includes:
   id
   title
   description
   price
   stock_quantity
   is_active
   category_id
   
## Inventory Management
Inventory management was implemented in Step 22.
# Each product has a:
   stock_quantity
   field representing the currently available stock.

# Cart Inventory Validation
   When adding a product to the cart:
   The requested quantity is checked against available stock.
   If the product already exists in the cart, the resulting total quantity is checked against available stock.
   Requests exceeding available stock are rejected.
# Example failure:
   HTTP 400
   Insufficient stock
This prevents users from placing more units in their cart than are currently available.

# Checkout Stock Reservation
   Checkout performs an atomic stock check and decrement.
   The product row is locked using SQLAlchemy:
   with_for_update()
      This uses PostgreSQL row-level locking.

# The checkout flow is effectively:
Start transaction
       |
       v
Lock product row
       |
       v
Check stock
       |
       +---- insufficient ----> rollback
       |
       v
Decrement stock
       |
       v
Create order
       |
       v
Create order items
       |
       v
Clear cart
       |
       v
Commit transaction
If any product does not have sufficient stock:
   Checkout fails
   The transaction is rolled back
   Stock is not partially decremented
   The order is not created
   The cart remains intact
   This provides atomic inventory handling during checkout.

## Shopping Cart
   User-specific cart
   Add product
   Increment product quantity
   Retrieve current cart
   Remove cart items
   JWT-protected cart operations
   Inventory validation before adding or incrementing products

Main endpoints:
   GET    /cart/
   POST   /cart/
   DELETE /cart/{item_id}

Inventory validation ensures that the cart quantity cannot exceed the currently available product stock.

## Orders / Checkout
   Checkout from the current user's cart
   Order and order-item creation
   Total calculation
   Product price locked into order items
   Cart cleared after successful checkout
   Order history
   Atomic stock reservation during checkout
   Row-level locking using PostgreSQL SELECT ... FOR UPDATE

Main endpoints:
   POST /orders/checkout
   GET  /orders/
   Checkout Transaction

The checkout transaction includes:

Stock validation
        +
Stock decrement
        +
Order creation
        +
Order item creation
        +
Cart cleanup

These operations are performed within the same database transaction.

## Mock Payment
   Payment processing endpoint
   Pending-order validation
   Order status changes to paid after successful payment
   UUID transaction ID generation
   Prevention of duplicate payment processing
Main endpoint:
   POST /payment/process

## Redis Caching
Redis is used for product catalog caching.
Cache keys include the relevant product-list parameters so different combinations of:
   Pagination
   Search
   Category filtering
do not incorrectly share cached responses.
Product creation invalidates the relevant catalog cache.
Redis is also used by the rate-limiting system and Celery.

## Rate Limiting
SlowAPI is integrated with Redis for rate-limit storage.
The login endpoint currently uses:
   5 requests / minute
This protects the login endpoint against repeated brute-force attempts.
Because Redis is used as the storage backend, rate-limit state is external to the FastAPI process.

## Celery Background Tasks
Celery is integrated with Redis as both broker and result backend.
Current infrastructure includes:
   app/core/celery_app.py
   app/tasks/email_tasks.py
and:
   celery_worker
as a dedicated Docker Compose service.
Celery configuration includes:
   JSON task serialization
   UTC configuration
   Redis broker
   Redis result backend
   Dedicated worker container

## Current task:
send_welcome_email_task
Successful user registration queues the task asynchronously.
If the broker cannot accept the task, the delivery failure is logged without undoing the successfully completed user registration.
The current welcome-email task intentionally simulates a slow email operation and logs a successful result.
It does not send a real email yet.

## Database
PostgreSQL is the primary relational database.
Current known tables:
   users
   categories
   products
   cart_items
   orders
   order_items
   alembic_version

SQLAlchemy is used as the ORM.
Alembic is used for database schema migrations.
Direct create_all schema management is no longer the application's migration strategy.
Schema changes are managed through Alembic migrations.

## Inventory Database Schema
The products table contains:
   stock_quantity
This field stores the currently available product quantity.
The inventory migration adds the stock field through Alembic rather than modifying the database manually.

## Current inventory migration:
3105be9533db_add_product_stock_quantity.py
   
## Alembic Schema Reconciliation
The reconciliation migration:
   b8c2d1e4f6a7
creates the catalog, cart, and order tables required by the current models in a fresh database and adds:
   users.is_superuser
It is designed to remain safe for the historical database that already contained these business tables before Alembic was introduced.

## API
Main endpoints currently include:
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
Protected endpoints require a valid JWT Bearer token.
Admin endpoints require a superuser account.

## Swagger / OpenAPI
After starting the application:
   http://127.0.0.1:8000/docs
Swagger is the primary tool used for manual API verification during development.
The OpenAPI specification is available at:
http://127.0.0.1:8000/openapi.json

## Running the Project
1. Activate the virtual environment
   source venv/bin/activate
2. Start Docker Compose
   docker compose up -d
   This starts:
      FastAPI
      PostgreSQL
      Redis
      Celery Worker
      3. Check containers
      docker compose ps

      Expected services:

      web
      db
      redis
      celery_worker
4. Open Swagger
   http://127.0.0.1:8000/docs
5. Check Celery worker logs
   docker compose logs -f celery_worker

## Database Migrations
Check the current Alembic revision:
   alembic current
Check available migration heads:
   alembic heads
Apply migrations:
   alembic upgrade head
Create a migration after changing SQLAlchemy models:
   alembic revision --autogenerate -m "describe change"
Always review generated migrations before applying them.
Never assume an autogenerated migration is correct without inspecting it.

## Testing
The project uses Pytest and HTTPX for automated API testing.
The test suite covers:
   Authentication
   Registration
   Login
   Protected routes
   Admin authorization
   Products
   Categories
   Cart
   Orders
   Payment
   Inventory validation
   Stock reduction
   Insufficient-stock checkout
   End-to-end shopping flow
   Security-related behavior
   Welcome-email task dispatch after registration

Run the test suite inside the Docker application container:
   docker compose exec web pytest
A development step is not considered complete until its relevant tests succeed.

## Latest Inventory Verification
Inventory-related tests verify:
   Adding more units than available stock
         ↓
   Rejected with HTTP 400
   Successful checkout
         ↓
   Product stock decreases correctly
   Insufficient stock during checkout
         ↓
   Checkout fails
         ↓
   Transaction rolls back

The complete verified test result for the current development step is:
10 passed

## CI/CD
GitHub Actions workflow:
   .github/workflows/ci.yml
The workflow:
   Builds the Docker environment
   Starts required services
   Waits for PostgreSQL
   Applies:
   alembic upgrade head
Runs the Pytest suite
The workflow runs on push and pull-request activity targeting:
   main

## Development Workflow
Every development step follows:
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
A step is not complete until its tests succeed.
## ######################    Important    ##############################
### Project Development Rules
      Do not move to the next step before the current step is tested.
      Documentation must be updated during development.
      Use one recommended solution instead of presenting unnecessary alternatives.
      Add useful comments to new or modified code.
      Commit and push after every completed step.
      Keep PROJECT_STATE.md synchronized with the real project state.
      Explain the reason for installations, files, tools, configuration changes, and code changes.
      Inspect existing code before modifying it.
      Do not remove existing functionality or data without checking its purpose and impact.
      Keep project state documented so development can continue in a new chat.
      Prefer inspection before modification.
      Never change database schema manually when the change should be represented by an Alembic migration.
      Review every autogenerated migration before applying it.
      Verify inventory-related changes with automated tests before considering them complete.
      Keep documentation chronological and consistent with the actual repository state.

## Current Development Progress
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

## Project Status
The latest completed development step is:
   Step 22 — Inventory Management and Atomic Stock Reservation
Inventory management is implemented for products, cart operations, and checkout.
The current system:
   Tracks available stock using stock_quantity
   Prevents adding more units to a cart than available
   Validates stock during checkout
   Locks product rows during checkout
   Atomically decrements stock
   Rolls back the transaction when stock is insufficient
   Creates orders and updates inventory within the same transaction
   Includes automated tests for inventory behavior

   The current welcome-email implementation remains a simulation rather than a real email-provider integration.

## Current Known-Good Development State
At the end of Step 22:
         FastAPI
            ↓
         PostgreSQL
            ↓
         Redis
            ↓
         Celery

## The application supports:

      Authentication
            +
      Authorization
            +
      Product Catalog
            +
      Search / Pagination
            +
      Redis Caching
            +
      Shopping Cart
            +
      Inventory Management
            +
      Atomic Stock Reservation
            +
      Order Checkout
            +
      Mock Payment
            +
      Rate Limiting
            +
      Celery Background Tasks
            +
      Alembic Migrations
            +
      Automated Tests
            +
      GitHub Actions CI

The current verified test result is:
   10 passed

## Future Roadmap
Planned areas include:
      Real email delivery integration
      Shipping management
      Administration expansion
      Refresh tokens
      Real payment gateway integration
      Structured logging
      Monitoring
      Metrics
      Distributed tracing
      Production configuration
      Security hardening
      API versioning
      Expanded automated test coverage
      Celery retry policies
      Celery task monitoring
      Additional background workflows for email, order processing, and notifications

## Documentation
The primary project-state document is:
   PROJECT_STATE.md
It contains the detailed:
   Architecture
   Completed development steps
   Current known-good state
   Lessons learned
   Repository status
   Pending work
   Future enhancements
   Development rules
   Next recommended step

PROJECT_STATE.md must remain synchronized with the actual repository state.

## Next Development Step
Before starting the next feature:
   Inspect the current repository state.
   Verify Docker Compose services.
   Verify PostgreSQL.
   Verify Redis.
   Verify Celery worker.
   Verify Celery task execution.
   Verify database migrations.
   Verify inventory behavior.
   Verify Redis caching.
   Verify rate limiting.
   Verify automated tests.
   Review Git status.
   Review documentation.
   Confirm GitHub repository state.
   Select the next development step.

No new feature should be implemented blindly.

The next step must be selected based on the actual repository state after inspection