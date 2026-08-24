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

### Current Step

Step 22 is the latest completed and verified development step.

Inventory management is now implemented for products, cart operations, and checkout.

Products have a `stock_quantity` field managed through Alembic.

The cart prevents users from adding more units than currently available. If a product already exists in the cart, the requested increment is validated against the product's current stock.

Checkout performs an atomic stock check and decrement using row-level locking with SQLAlchemy `with_for_update()`.

Stock decrement, order creation, and cart cleanup occur inside the same database transaction.

Automated inventory and checkout tests have been verified successfully.

Latest verified targeted shopping test result:


5 passed

Latest broader test verification:

10 passed


# 3. Current Architecture
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
       |       +---- Order items
       |       +---- Price locking
       |       +---- Atomic stock reservation
       |       +---- Order history
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

# 4. Technology Stack
Python 3.12 slim Docker base image
FastAPI 0.104.1
Uvicorn
PostgreSQL 15 Alpine
SQLAlchemy 2.x
Redis 7 Alpine
Redis Python client
JWT authentication
Alembic 1.13.1
Docker
Docker Compose
Pytest
HTTPX
SlowAPI
Celery 5.3.6
Swagger / OpenAPI
GitHub Actions

The project uses Redis for caching, rate limiting, and Celery infrastructure.

# 5. Implemented Features
# 5.1 Application
FastAPI application
Uvicorn development server
Environment-based configuration
Swagger / OpenAPI documentation
Health endpoint
SQLAlchemy database session management
Dockerized application

# 5.2 User Management
User registration
Duplicate email detection
Password hashing
User login
JWT access token generation
Invalid credential handling
Current authenticated user endpoint
is_superuser support

# 5.3 Authentication and Authorization
JWT Bearer authentication
get_current_user dependency
Protected routes
OAuth2 password form compatibility using python-multipart
get_current_admin_user dependency
Admin-only protected endpoints
Regular users receive HTTP 403 on admin-only endpoints
Superusers receive HTTP 200 on admin-only endpoints

# 5.4 Product Catalog

Category model:

id
name
description

Product model:

id
title
description
price
stock_quantity
is_active
category_id

Catalog endpoints:

GET  /categories/
POST /categories/
GET  /products/
POST /products/

POST /categories/ and POST /products/ are admin-only.

Product listing supports:

skip / limit pagination
search filtering by title
Case-insensitive title search using SQLAlchemy ilike
category_id filtering
Redis caching

Redis cache keys include all relevant product-list parameters.

Product creation invalidates existing product-list cache entries.

# 5.5 Shopping Cart

Implemented:

CartItem SQLAlchemy model
Pydantic cart schemas
User-specific cart isolation
GET /cart/
POST /cart/
DELETE /cart/{item_id}
JWT protection using get_current_user

Inventory validation:

Adding a product validates the requested quantity against stock_quantity.
Increasing an existing cart item validates the resulting quantity against current stock.
Requests exceeding available stock return HTTP 400.
The error detail is:
Insufficient stock

# 5.6 Orders

Implemented:

Order SQLAlchemy model
OrderItem SQLAlchemy model
Checkout flow
POST /orders/checkout
GET /orders/
Cart-to-order conversion
Order total calculation
Unit price locking
Cart cleanup after successful checkout
User order history
Inventory Reservation During Checkout

Checkout uses database row-level locking:

.with_for_update()

The checkout process:

Retrieves the user's cart.
Checks that the cart is not empty.
Locks each required product row.
Verifies sufficient stock while the row is locked.
Decrements stock_quantity.
Creates the order items.
Creates the main order.
Clears the user's cart.
Commits everything in one transaction.

If any product does not have enough stock:

HTTP 400

is returned and the transaction is rolled back.

This prevents a partial checkout where some stock is reduced while the order fails.

# 5.7 Mock Payment

Implemented:

Mock payment module
POST /payment/process
Pending-order validation
Successful payment changes order status to paid
UUID-based transaction ID generation
Already-paid orders cannot be processed again

# 5.8 Automated Testing

Pytest is configured for the project.

Implemented test coverage includes:

Authentication tests
Registration tests
Login tests
Protected /users/me tests
Product tests
Cart tests
Order tests
Payment tests
End-to-end shopping flow tests
Inventory validation tests
Checkout stock reduction tests
Insufficient-stock checkout tests

Centralized fixtures provide:

TestClient
Test-user creation
Authentication token generation
Test-user cleanup

The project tests are executed inside Docker using:

docker compose exec web pytest
Inventory Test Coverage

The inventory implementation is specifically tested for:

Adding more than available stock → rejected
Checkout with sufficient stock → stock reduced
Checkout with insufficient stock → rejected
Full shopping flow → successful

Targeted shopping tests were successfully verified with:

docker compose exec web pytest tests/test_shop.py -vv -x

Result:

5 passed

# 5.9 CI/CD

GitHub Actions workflow:

.github/workflows/ci.yml

The workflow:

Builds the Docker environment.
Starts required services.
Waits for PostgreSQL.
Applies Alembic migrations.
Runs the Pytest suite.

CI is triggered by push and pull-request activity targeting main.

# 5.10 Database Migrations

Alembic is the application's database schema management system.

Implemented:

Alembic initialization
Alembic configuration
SQLAlchemy metadata integration
Initial historical migration
Existing database baseline
Schema reconciliation migration
Migration-aware CI
Automated migration execution before tests

Initial historical migration:

aee86fd59c30

Schema reconciliation migration:

b8c2d1e4f6a7

Inventory migration:

3105be9533db_add_product_stock_quantity.py

The inventory migration adds:

products.stock_quantity

to the product schema.

The existing database was originally registered with:

alembic stamp head

to prevent Alembic from attempting to recreate existing business tables.

# 5.11 Redis Caching

Redis is used for product catalog caching.

Implemented:

Redis 7 Docker service
Redis connection through application configuration
Dynamic product-list cache keys
Pagination-aware cache keys
Search-aware cache keys
Category-filter-aware cache keys
Product cache invalidation after product creation

Example cache-key structure:

products_list:{skip}:{limit}:{search}:{category_id}

# 5.12 Inventory Management

Inventory management was introduced in Step 22.

Product inventory is represented by:

stock_quantity

The stock quantity represents the currently available units of a product.

Cart-level protection:

Users cannot add more units than currently available.
Existing cart quantities are checked when additional units are added.
Requests exceeding stock return HTTP 400.

Checkout-level protection:

Product rows are locked with SELECT ... FOR UPDATE.
Stock is checked while the row is locked.
Stock is decremented inside the same transaction as order creation.
Cart cleanup occurs in the same transaction.
Insufficient stock causes checkout to fail.
Database rollback prevents partial stock updates.

This provides an atomic inventory reservation mechanism for the current checkout implementation.

# 5.13 Rate Limiting

SlowAPI is integrated with FastAPI.

Redis is used as the rate-limit storage backend.

The login endpoint is protected with:

5 requests per minute

This protects authentication against repeated login attempts and brute-force behavior.

# 5.14 Celery Background Processing

Celery is integrated as the background task processing layer.

Current implementation:

Celery 5.3.6
Shared Celery application
Redis as broker
Redis as result backend
JSON task serialization
UTC configuration
Dedicated celery_worker Docker Compose service
Welcome-email task
Asynchronous task dispatch after successful registration

Celery application:

app/core/celery_app.py

Background tasks:

app/tasks/email_tasks.py

Current task:

send_welcome_email_task

The current welcome-email task intentionally simulates a slow email operation.

It does not send a real email yet.

Worker command:

celery -A app.core.celery_app.celery_app worker --loglevel=info

# 6. Database

PostgreSQL is the primary relational database.

Current known tables:

users
categories
products
cart_items
orders
order_items
alembic_version

Product inventory is stored in:

products.stock_quantity

SQLAlchemy is used as the ORM.

Alembic manages database schema migrations.

Direct SQLAlchemy create_all() is not the application's schema-management strategy.

Database schema changes must be introduced through Alembic migrations.

# 7. Docker

Current Docker Compose services:

db
redis
web
celery_worker
db
PostgreSQL 15 Alpine
Persistent postgres_data volume
Internal backend_network
Host port exposure disabled
redis
Redis 7 Alpine
Internal backend_network
Host port 6379 currently mapped
Product caching
Rate-limit storage
Celery broker
Celery result backend
web
Built from the project Dockerfile
Python 3.12 slim
FastAPI + Uvicorn
Port 8000
Uses .env
Depends on PostgreSQL and Redis
celery_worker
Built from the same Docker image
Runs Celery worker
Uses .env
Depends on Redis and PostgreSQL
Shares backend_network

# 8. Current Known Good State

## Step 1 — Project Setup
Repository verified.
Main branch verified.
Python virtual environment verified.
Initial project structure inspected.

Status: Completed

## Step 2 — Configuration and Security
Application configuration implemented.
Environment variables used.
Database URL generated from configuration.
JWT configuration implemented.
Password hashing implemented.
JWT generation tested successfully.

Status: Completed

## Step 3 — User Module
User model implemented.
User schemas implemented.
User router implemented.
User registration implemented.
User login implemented.
User routes verified.

Status: Completed

## Step 4 — PostgreSQL and Authentication

Successfully verified:

PostgreSQL Docker container
Database connection
users table
FastAPI startup
Health check
User registration
Duplicate email detection
User login
JWT generation
Invalid password handling

Swagger was used for manual API verification.

Status: Completed

## Step 5 — Alembic

Successfully implemented:

Alembic initialization
Alembic configuration
SQLAlchemy metadata integration
Initial migration
Existing database baseline

Historical revision:

aee86fd59c30

Status: Completed

## Step 6 — Dockerization

Implemented:

FastAPI Dockerfile
Python 3.12 slim base image
requirements.txt
FastAPI Docker Compose service
PostgreSQL Docker service
Redis Docker service
Internal Docker network

Status: Completed

## Step 7 — JWT Protected Routes

Implemented:

get_current_user
JWT Bearer token validation
Protected /users/me
OAuth2 form compatibility

Verified with a valid JWT.

Status: Completed

## Step 8 — RBAC / Admin Authorization

Implemented:

is_superuser
Admin authorization dependency
get_current_admin_user
Admin-only endpoint

Verified:

Regular user → HTTP 403
Superuser     → HTTP 200

Status: Completed

## Step 9 — Product and Category Catalog

Implemented:

Category model
Product model
Category/Product relationship
Category schemas
Product schemas
Public category endpoint
Public product endpoint
Admin-only category creation
Admin-only product creation

Verified through Swagger.

Status: Completed

## Step 10 — Product Catalog Upgrade

Implemented:

skip
limit
search
Case-insensitive title search using ilike
category_id filtering

Successfully tested through Swagger.

Status: Completed

## Step 11 — Cart Management

Implemented:

cart_items table
User/product relationships
User-specific cart retrieval
Add/increment products
Cart-item removal
JWT protection

Status: Completed

## Step 12 — Order Checkout

Implemented:

orders table
order_items table
Checkout
Cart-to-order conversion
Order total calculation
Unit-price locking
Cart cleanup
Order history

Status: Completed

## Step 13 — Mock Payment

Implemented:

POST /payment/process
Pending-order validation
Successful payment status update
UUID transaction IDs
Duplicate-payment protection

Status: Completed

## Step 14 — Automated Testing

Implemented:

Pytest
HTTPX
Reusable fixtures
Test database cleanup
Test-user factory
JWT token fixture
Authentication tests
Registration tests
Login tests
Protected-route tests

Verification:

docker compose exec web pytest

Status: Completed

## Step 15 — E2E Shopping Flow

Implemented:

Product browsing test
Cart operation test
Checkout test
Payment test
Complete purchase lifecycle test

Verification:

docker compose exec web pytest tests/test_shop.py -vv -x

Status: Completed

## Step 16 — GitHub Actions CI

Implemented:

.github/workflows/ci.yml
Push trigger
Pull-request trigger
Docker environment
Automated Pytest execution

Status: Completed

## Step 17 — Alembic Schema Management

Implemented:

Alembic integration
Existing PostgreSQL schema synchronization
Initial migration
Baseline stamping
Removal of direct create_all() schema management
Migration-based schema management

Status: Completed

## Step 18 — Redis Product Caching

Implemented:

Redis product cache
Dynamic cache keys
Pagination-aware caching
Search-aware caching
Category-aware caching
Cache invalidation after product creation

Status: Completed

## Step 19 — Rate Limiting

Implemented:

SlowAPI
Redis-backed rate limiting
Login protection
5/minute login limit

During testing, repeated login requests can intentionally trigger:

ratelimit 5 per 1 minute

The test fixtures were adjusted so the rate-limit state does not interfere with normal authentication tests.

Status: Completed

## Step 20 — Celery Background Worker

Implemented:

Celery 5.3.6
Shared Celery application
Redis broker
Redis result backend
JSON serialization
UTC configuration
celery_worker service
Welcome-email task
Asynchronous task dispatch after registration

The current email task is simulated and does not send real email.

Status: Completed and verified

## Step 21 — Alembic Schema Reconciliation and Migration-Aware CI

Implemented:

Schema reconciliation migration
Missing catalog tables
Missing cart tables
Missing order tables
users.is_superuser
Fresh-database compatibility
Historical-database safety
Migration-aware CI

CI applies:

alembic upgrade head

before running tests.

Status: Completed and verified

## Step 22 — Inventory Management and Atomic Stock Reservation

Implemented:

Added stock_quantity to the Product model.
Added the corresponding Alembic migration.
Updated product schemas to expose inventory information.
Added stock validation to cart operations.
Prevented adding more units than available stock.
Prevented increasing an existing cart item beyond available stock.
Added atomic stock checking during checkout.
Added row-level locking with with_for_update().
Decremented stock inside the checkout transaction.
Preserved transaction rollback behavior when stock is insufficient.
Added automated inventory tests.
Verified the full shopping flow after inventory changes.

Inventory migration:

alembic/versions/3105be9533db_add_product_stock_quantity.py

Targeted verification:

docker compose exec web pytest tests/test_shop.py -vv -x

Result:

5 passed

Broader verification:

10 passed

Status: Completed and verified

# 9. Major Lessons Learned
Windows PostgreSQL occupied host port 5432 during development.
WSL PostgreSQL also used port 5432 during troubleshooting.
Local PostgreSQL services were stopped because this is a test/development environment.
Docker PostgreSQL is the project's database.
The application entry point is main.py in the repository root.
Docker Compose uses the db service name for PostgreSQL connectivity.
PostgreSQL host port exposure was disabled to improve network isolation.
Redis is intentionally shared by caching, rate limiting, and Celery.
The original users table existed before Alembic was introduced.
Alembic autogeneration initially produced an empty migration because the table already existed.
alembic stamp head was used to establish the existing database as the migration baseline.
Direct SQLAlchemy create_all() schema management was removed in favor of Alembic.
Swagger is the primary tool used for manual API verification.
Product and category creation are protected by admin authorization.
Product-list caching must account for pagination, search, and category filters in its cache key.
Product creation requires cache invalidation so newly created products can appear in subsequent catalog responses.
Login rate limiting uses Redis so the limit is stored outside the FastAPI process.
Celery uses Redis as its broker/result backend, allowing long-running tasks to execute outside the request/response path.
The current welcome-email task is a simulation and does not send real email.
Inventory validation must happen both at cart time and checkout time.
Cart-time stock validation improves user experience but cannot guarantee stock availability at checkout.
Checkout must re-check stock inside a database transaction.
SELECT ... FOR UPDATE prevents concurrent checkout transactions from modifying the same product stock simultaneously.
Stock decrement and order creation must remain part of the same transaction.
If checkout fails because of insufficient stock, the transaction must roll back without partially reducing inventory.

# 10. Repository Status

Repository:

maherani/ecommerce_backend

Branch:

main

GitHub is the source-control repository.

Development history through the inventory implementation has been developed incrementally and verified locally.

Current working-tree changes related to Step 22 include:

app/modules/cart/router.py
app/modules/order/router.py
app/modules/product/models.py
app/modules/product/schemas.py
tests/conftest.py
tests/test_shop.py
alembic/versions/3105be9533db_add_product_stock_quantity.py

The latest git diff --check completed without output, indicating no whitespace errors were detected.

The Step 22 changes should be committed and pushed only after the documentation has been synchronized and the final test suite has been verified.

# 11. Important Project Files
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

Important application infrastructure files:

app/core/config.py
app/core/database.py
app/core/security.py
app/core/cache.py
app/core/rate_limit.py
app/core/celery_app.py
app/tasks/email_tasks.py

Major business modules:

app/modules/user/
app/modules/product/
app/modules/cart/
app/modules/order/
app/modules/payment/

Important test files:

tests/conftest.py
tests/test_shop.py

PROJECT_STATE.md is the primary project memory document and must remain synchronized with the real repository state.

# 12. Pending Work
Immediate
Synchronize PROJECT_STATE.md and README.md with the verified Step 22 implementation.
Run the complete test suite.
Review the Step 22 Git diff.
Verify Alembic migration status.
Verify Docker Compose services.
Commit Step 22.
Push Step 22 to GitHub.
Only then select the next development step.
Planned Features
Shipping management
Administration expansion
Real email delivery integration
Structured logging
Monitoring and observability
Metrics
Distributed tracing
Production hardening
Production configuration
Security hardening
API versioning
Expanded automated test coverage
Celery retry policies
Celery task monitoring
Advanced background workflows
Real payment gateway integration
Completed Roadmap Items
Shopping cart — Done
Order checkout and order management — Done
Mock payment simulation — Done
Alembic database migrations — Done
Product catalog pagination and search — Done
Redis product caching — Done
Rate limiting — Done
Pytest automated testing — Done
E2E shopping-flow testing — Done
GitHub Actions CI — Done
Celery worker infrastructure — Done
Alembic schema reconciliation — Done
Migration-aware CI — Done
Inventory management — Done
Atomic stock reservation during checkout — Done

# 13. Future Enhancements
Stronger password validation
Refresh tokens
Real payment gateway integration
Real email provider integration
Shipping management
Rate limiting improvements for additional sensitive endpoints
Redis caching expansion
Structured logging
Monitoring
Metrics
Distributed tracing
Production configuration
Security hardening
API versioning
Expanded automated test coverage
Celery retry policies and task monitoring
Dedicated background task workflows for email, order processing, and notifications
Inventory reservation expiration
Stock restoration after order cancellation
Inventory audit history
Admin inventory management endpoints

# 14. Next Recommended Step

Do not start a new feature blindly.

Before selecting the next step, verify:

Project structure
Docker Compose services
Celery worker status
Celery task execution
Database models
API routers
Schemas
Tests
Alembic migrations
Redis cache
Rate limiting
Inventory implementation
GitHub Actions
README
PROJECT_STATE.md
Git status
GitHub repository status

The immediate priority is to complete the Step 22 documentation and repository workflow:

1. Update README.md
2. Verify PROJECT_STATE.md
3. Run complete test suite
4. Review git diff
5. Verify Alembic status
6. Commit Step 22
7. Push to GitHub
8. Verify GitHub Actions
9. Only then select Step 23

No new feature should be started before Step 22 is committed, pushed, and verified in CI.

# 15. Development Rules
No step is complete without a successful test.
Do not move to the next step before the current step is tested.
Documentation must be updated during development.
Use one recommended solution instead of presenting unnecessary alternatives.
Add useful comments to new or modified code.
Commit and push after every completed step.
Keep PROJECT_STATE.md synchronized with the actual project state.
Explain the reason for every installation, file creation, tool usage, code change, and configuration change.
Keep the project state clear enough to continue development in a new chat.
Before starting a new development step, verify documentation and GitHub state.
Prefer inspection before modification.
Never remove existing data or functionality without first verifying its purpose and impact.
When a feature is marked completed, record what was implemented and how it was verified.
Keep the documentation clean and chronological so a new development session can resume without relying on previous chat history.
Inventory changes must be managed through Alembic migrations.
Stock availability must be re-checked during checkout even if it was already checked while adding the product to the cart.
Stock decrement and order creation must occur in the same database transaction.
Use row-level locking for concurrent inventory updates.
Do not mark an implementation step as complete until both targeted tests and the broader test suite have been verified.
Review documentation before every Git commit.
Do not recommend git push until documentation and tests have been reviewed.
Preserve existing functionality unless a change is explicitly required and verified.


# 16. Current Development Baseline

The project currently represents a Dockerized, testable FastAPI e-commerce backend with:

FastAPI
PostgreSQL
SQLAlchemy
Alembic
Redis
JWT Authentication
RBAC
Product Catalog
Search
Pagination
Category Filtering
Redis Caching
Shopping Cart
Inventory Management
Atomic Stock Reservation
Order Checkout
Mock Payment
Rate Limiting
Celery
Background Tasks
Pytest
End-to-End Tests
GitHub Actions CI
Docker Compose

The current known-good development milestone is:

Step 22 — Inventory Management and Atomic Stock Reservation

The repository should be committed and pushed at the end of this milestone before beginning the next feature.