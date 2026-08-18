# E-Commerce Backend

Production-oriented e-commerce backend built with FastAPI, PostgreSQL, Redis, SQLAlchemy, JWT authentication, Alembic, and Docker.

The project is developed incrementally with testing, documentation, Git version control, and GitHub synchronization after every completed development step.

## Project Objective

Build a maintainable and production-oriented backend for an e-commerce platform.

The project focuses on:

- Clean architecture
- Authentication and authorization
- Database migrations
- Containerization
- Automated testing
- Documentation
- Security
- Observability
- CI/CD
- Production readiness

## Technology Stack

- Python
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy
- Redis
- JWT Authentication
- Alembic
- Docker
- Docker Compose
- Swagger / OpenAPI

## Current Architecture

```text
Client / Frontend
       |
       v
    FastAPI
       |
       +---- Users
       +---- Authentication
       +---- RBAC
       +---- Categories
       +---- Products
       |
       v
   PostgreSQL

Redis
  |
  +---- Future caching/features
```

## Current Docker Architecture

```text
Docker Compose
│
├── web
│    └── FastAPI
│
├── db
│    └── PostgreSQL
│
└── redis
     └── Redis
```

All services communicate through:

```text
backend_network
```

PostgreSQL and Redis are not directly exposed to the host.

## Current Features

### User Authentication

- User registration
- Password hashing
- User login
- JWT access tokens
- Invalid credential handling
- JWT Bearer authentication
- Current authenticated user
- Protected routes

### Authorization

Role-based authorization is implemented using the `is_superuser` field.

Admin-only routes use:

```text
get_current_admin_user
```

Regular users receive HTTP 403 when accessing admin-only endpoints.

### Product Catalog

Categories:

```text
GET /categories/
POST /categories/    # Admin
```

Products:

```text
GET /products/
POST /products/      # Admin
```

Products are associated with categories using a foreign key.

## Database

PostgreSQL is the primary relational database.

Current database tables:

```text
users
categories
products
alembic_version
```

SQLAlchemy is used as the ORM.

Alembic is used for database schema migrations.

## Redis

Redis is included in Docker Compose and connected to the internal backend network.

It is currently reserved for future features such as:

- Caching
- Rate limiting
- Temporary data
- Other application-level optimizations

## API

Current main endpoints:

```text
GET  /
POST /users/
POST /users/login
GET  /users/me
GET  /users/admin-only

GET  /categories/
POST /categories/

GET  /products/
POST /products/
```

Protected endpoints require a valid JWT Bearer token.

Admin endpoints require a superuser account.

## Swagger

After starting the application:

```text
http://127.0.0.1:8000/docs
```

Swagger is currently the primary tool used for manual API testing.

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

### 3. Check containers

```bash
docker compose ps
```

### 4. Open Swagger

```text
http://127.0.0.1:8000/docs
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

## Testing Status

Successfully verified during development:

- PostgreSQL Docker startup
- Database connection
- Database table creation
- FastAPI startup
- Health check
- User registration
- Duplicate email detection
- User login
- JWT generation
- Invalid password handling
- JWT protected `/users/me`
- Admin authorization
- Regular-user HTTP 403 behavior
- Admin HTTP 200 behavior
- Category creation
- Product creation
- Public category listing
- Public product listing
- Docker Compose application stack

Swagger has been used extensively for manual API verification.

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
10. Keep the project state documented so development can continue in a new chat.

## Current Development Progress

```text
Step 1  — Project Setup                 ✅
Step 2  — Configuration & Security     ✅
Step 3  — User Module                  ✅
Step 4  — PostgreSQL & Authentication  ✅
Step 5  — Alembic                      ✅
Step 6  — Dockerization                ✅
Step 7  — JWT Protected Routes         ✅
Step 8  — RBAC / Admin Authorization   ✅
Step 9  — Product & Category Catalog   ✅
Step 10 — Next development phase       ⏳
```

## Future Roadmap

Planned areas include:

- Automated test suite
- Inventory management
- Shopping cart
- Orders
- Payments
- Shipping
- Administration
- Redis caching
- Structured logging
- Monitoring
- Metrics
- CI/CD
- Production hardening
