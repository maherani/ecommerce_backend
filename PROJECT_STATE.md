# PROJECT_STATE

## Objective
Build a production-oriented e-commerce platform with a FastAPI backend and React/TypeScript frontend, backed by PostgreSQL and Redis, with JWT authentication, Alembic, Docker, Pytest, GitHub Actions, SlowAPI, Celery, inventory management, payment persistence, refunds, payment idempotency, audit history, payment webhooks, security hardening, observability, and production-readiness practices.

## Current Architecture

```text
Client / React Frontend
        ↓
     FastAPI
        ├── User
        ├── Product / Category
        ├── Cart
        ├── Order / OrderItem
        │     ├── Shipping (1:1)
        │     └── Payment  (1:1)
        │             └── PaymentEvent (1:N)
        ├── Rate Limiting
        ├── Observability
        │     ├── Prometheus metrics
        │     ├── Request logging
        │     ├── Request ID / correlation
        │     └── Grafana dashboards
        └── Background Tasks
              └── Celery Worker

PostgreSQL ← application data
Redis      ← cache / rate limiting / Celery broker/backend
Prometheus ← API metrics scraping
Grafana    ← Prometheus visualization
```

## Completed Steps

Steps 1–25 completed, followed by:

- Step 30 — Persistent payment records
- Step 31 — Payment refund flow
- Step 32 — Payment idempotency
- Step 33 — Payment audit history
- Step 34 — Rich payment audit metadata
- Step 35 — Payment webhooks
- Step 36 — Webhook Delivery & Retry Infrastructure
- Step 37 — Security & API Hardening
- Step 38 — Observability
- Step 39 — Frontend foundation and API integration
- Step 40 — Frontend authentication
- Step 41 — Frontend Product Details

## Implemented Features

### Orders
Checkout performs stock reservation and creates Order/OrderItems/Shipping transactionally, with rollback on failure. Order lifecycle supports pending, paid, processing, shipped, delivered, and cancelled states.

### Payment and Webhooks
Steps 30–36 implement persistent payments, refunds, idempotency, immutable audit events, rich metadata, HMAC-protected webhooks, Celery/Redis asynchronous processing, and transient retry handling with maximum 3 retries.

### Security & API Hardening — Step 37
JWT access-token claims include `exp`, `iat`, and `type=access`. Password minimum length is 8. Security headers, configuration-driven CORS, startup validation of sensitive settings, and safe generic 500 responses are implemented.

The development frontend runs on Vite's default port `5173`. CORS is configured for:

```text
http://localhost:5173
http://127.0.0.1:5173
```

### Observability — Step 38

Metrics:

```text
http_requests_total
http_request_duration_seconds
```

Metrics are exposed at `GET /metrics`. Prometheus scrapes `web:8000/metrics` every 5 seconds using the `ecommerce_api` job.

Request logs contain `method`, `path`, `status`, `request_id`, and `duration_ms`. `X-Request-ID` is preserved when supplied and generated as a UUID when absent. Unhandled exceptions retain request correlation in logs and are represented as HTTP 500 metrics.

### Grafana Dashboard — Step 38 Extension

Grafana is deployed through Docker Compose and uses the persistent `grafana_data` volume.

Current dashboard:

```text
Dashboard: Dashbourd 1
```

Current five panels:

```text
1. API Request Rate
2. API Request Latency (P95)
3. API Error Rate
4. Requests by Endpoint
5. HTTP Requests by Status
```

### Frontend — Step 39

A React + TypeScript frontend was initialized with Vite under:

```text
frontend/
```

Current frontend foundation includes:

```text
React 19
TypeScript
Vite
Oxlint
```

The frontend has been verified locally with:

```text
npm run build  → green
npm run lint   → green
```

The frontend successfully communicates with the running API and displays products returned by:

```text
GET /products/
```

The initial product UI includes reusable product-card/grid components and application pages/layouts/services/types. Product data has been verified in the browser.

The Step 39 frontend implementation has been committed and pushed to the remote `main` branch.

### Frontend Authentication — Step 40

The frontend now supports JWT authentication through the FastAPI authentication API.

Implemented flow:

```text
Login Page
    ↓
POST /users/login
    ↓
JWT access_token
    ↓
localStorage
    ↓
authenticatedFetch()
    ↓
Authorization: Bearer <JWT>
    ↓
GET /users/me
    ↓
Authenticated User displayed in UI
```

Runtime verification completed successfully:

```text
Login successful
access_token present in Local Storage
Authenticated user displayed
```

### Frontend Product Details — Step 41

The frontend now supports navigation from the product list to a dedicated product detail page.

Implemented flow:

```text
Products Page
    ↓
ProductCard
    ↓
View Product
    ↓
/products/:productId
    ↓
ProductDetailsPage
    ↓
GET /products/{product_id}
    ↓
Product Details displayed
```

The backend provides `GET /products/{product_id}` and returns `404` when the requested product does not exist.

The Product Details page loads the product by route parameter, handles loading and error states, and displays title, description, price, and stock status.

Runtime verification completed successfully in the browser:

```text
/products
    ↓
View Product
    ↓
/products/1
    ↓
Product details displayed successfully
```

## Testing

Latest full-suite verification:

```text
56 passed
```

Command:

```bash
docker compose exec web pytest -q
```

Frontend verification:

```bash
cd frontend
npm run build
npm run lint
```

Both frontend commands were verified green locally.

### Test Database Isolation

Automated tests use a dedicated PostgreSQL database named `ecommerce_db_test` instead of the development database.

The test setup creates the test database when needed, configures the test database URL before importing the application database session, and applies the Alembic head migration to the test database.

Verified separation:

```text
ecommerce_db       → development data
 e-commerce_db_test → test data
```

The latest test run completed with 56 passing tests and the development database user data remained separate from test cleanup.

The GitHub Actions workflow currently verifies the Dockerized backend build, migrations, and Pytest suite; it does not yet run the frontend build/lint commands.

## Database Migration Chain

```text
40f98fd888bb_add_shipping_table.py
                ↓
cff58edd10a9_add_payments_table.py
                ↓
aea3438feb25_add_payment_idempotency_key.py
                ↓
e124ed32b079_add_payment_events_table.py
                ↓
2a408bf8badb_add_payment_audit_metadata.py
                ↓
e3e6a6bd5e42_add_payment_webhook_event_id.py
```

Steps 37–41 add no database migration.

## Repository Status

The latest frontend Product Details implementation and test database isolation changes are committed and pushed to the remote `main` branch.

Latest verified backend suite:

```text
56 passed
```

Latest verified frontend checks:

```text
npm run build → green
npm run lint  → green
```

The current GitHub Actions workflow remains green for the backend Docker/pytest pipeline. Frontend build and lint are verified locally but are not yet separate CI checks.

## Current Known Good State

```text
Step 36 — Webhook Delivery & Retry        COMPLETED
Step 37 — Security & API Hardening        COMPLETED
Step 38 — Observability                   IMPLEMENTED
Step 39 — Frontend foundation             IMPLEMENTED AND PUSHED
Step 40 — Frontend authentication         IMPLEMENTED AND PUSHED
Step 41 — Product Details                 IMPLEMENTED AND PUSHED
Grafana Dashboard                         IMPLEMENTED
Grafana Panels                            5
Backend Tests                             56 passed
Frontend Build                            GREEN
Frontend Lint                             GREEN
Test Database                             ISOLATED
Alembic head                              e3e6a6bd5e42
```

## Major Lessons Learned

- Alembic is the authoritative schema-management mechanism.
- Database uniqueness is required in addition to application checks for payment idempotency.
- Webhooks require signature verification and their own idempotency mechanism.
- Asynchronous webhook processing should be separated from the HTTP request path.
- Only transient infrastructure failures should trigger automatic retries.
- JWT tokens should carry explicit access-token semantics.
- CORS should be explicitly configured instead of using wildcard origins.
- Sensitive configuration should be validated during startup.
- Unexpected application errors should not expose internal details to clients.
- Prometheus metrics provide machine-readable signals for request rate and latency.
- Request IDs make logs traceable across individual HTTP requests.
- Grafana provides the visualization layer for Prometheus metrics and makes operational trends easier to inspect.
- A Vite React frontend must use the actual development origin (`localhost:5173`) in backend CORS configuration.
- Frontend dependency/runtime versions must be compatible with the installed Node.js version.
- Backend API behavior should be verified from generated OpenAPI data before implementing frontend API integrations.
- Automated tests must run against a dedicated test database and must not share the development database.
- The test suite now creates and migrates a separate `ecommerce_db_test` database.
- Payment and refund remain mock provider operations.

## Pending Work

- Continue frontend cart, checkout, and order UI flows.
- Add frontend build and lint checks to GitHub Actions CI.
- Keep documentation synchronized after each frontend milestone.

## Future Enhancements

- Real payment gateway integration
- Structured JSON logging
- Distributed tracing
- API versioning
- Advanced inventory policies
- Production alerting and SLO-based monitoring
- Additional Grafana dashboards and alert rules
- Product detail and catalog filtering/search
- Customer session management and token lifecycle improvements
- Cart and checkout UI

## Next Recommended Step

Implement the frontend cart flow, then continue with checkout and order UI. In parallel, add frontend build/lint validation to GitHub Actions.

## Notes For Future Sessions

Start with:

```bash
git status --short
git log -1 --oneline
docker compose ps
docker compose exec web pytest -q
cd frontend && npm run build && npm run lint
cd .. && docker compose exec web alembic current
```
