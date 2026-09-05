# E-Commerce Platform

Production-oriented e-commerce platform with a FastAPI backend and a React/TypeScript frontend, backed by PostgreSQL, Redis, Celery, Prometheus, and Grafana.

## Architecture

```text
Client / React Frontend
        |
        v
     FastAPI
        |
        +---- User
        +---- Product / Category
        +---- Cart
        +---- Order / OrderItem
        |       +---- Shipping (1:1)
        |       +---- Payment (1:1)
        |               +---- PaymentEvent (1:N)
        +---- Rate Limiting
        +---- Observability
        |       +---- Prometheus metrics
        |       +---- Request logging
        |       +---- Request ID / correlation
        |       +---- Grafana dashboards
        +---- Background Tasks
                +---- Celery Worker

PostgreSQL ← application data
Redis      ← cache / rate limiting / Celery broker/backend
Prometheus ← API metrics scraping
Grafana    ← Prometheus visualization
```

Docker Compose services: `db`, `redis`, `web`, `celery_worker`, `prometheus`, and `grafana`.

## Backend

The backend provides JWT authentication, user/admin authorization, product and category management, cart and checkout flows, shipping, payment processing, refunds, payment idempotency, immutable payment audit events, HMAC-protected webhooks, asynchronous webhook processing, security hardening, and Prometheus/Grafana observability.

### CORS

The development React frontend runs on Vite's default port `5173`. The backend is configured to allow:

```text
http://localhost:5173
http://127.0.0.1:5173
```

### Payment

#### Step 30 — Persistent Payment Records
`POST /payment/process` persists Payment state, creates a unique transaction ID, records `paid_at`, and changes a pending order to paid.

#### Step 31 — Payment Refund
`POST /payment/{order_id}/refund` validates ownership and paid state, prevents duplicate refunds, records `refunded_at`, and preserves the original transaction ID. The provider operation remains simulated.

#### Step 32 — Payment Idempotency
`POST /payment/process` accepts an optional `idempotency_key`, persisted with the unique constraint `uq_payments_idempotency_key`.

#### Step 33 — Payment Audit History
The `payment_events` table stores immutable payment state-change events.

#### Step 34 — Rich Payment Audit Metadata
Payment events include `actor_user_id` and structured JSON metadata.

#### Step 35 — Payment Webhooks
`POST /payment/webhook` validates an HMAC-SHA256 signature, checks `event_id` idempotency, validates the transaction and status, and records an audit event.

#### Step 36 — Webhook Delivery & Retry Infrastructure
Webhook processing is asynchronous through Celery and Redis. Transient `ConnectionError` failures are retried up to 3 times with backoff.

#### Step 37 — Security & API Hardening
JWT access-token claims, password minimum length, security response headers, configuration-driven CORS, startup security validation, and safe generic 500 responses are implemented.

#### Step 38 — Observability
The API exposes:

```text
http_requests_total
http_request_duration_seconds
```

Prometheus scrapes `web:8000/metrics` every 5 seconds through the `ecommerce_api` job.

Grafana provides the visualization layer with five current panels: request rate, P95 latency, error rate, requests by endpoint, and HTTP requests by status.

## Frontend

### Step 39 — Frontend Foundation

The initial frontend was created with Vite using React and TypeScript:

```text
frontend/
├── React 19
├── TypeScript
├── Vite
└── Oxlint
```

The frontend has reusable application layouts, pages, components, API services, and TypeScript types. Product data is integrated with the backend and verified in the browser through `GET /products/`.

Frontend validation was verified locally:

```text
npm run build → green
npm run lint  → green
```

### Step 40 — Frontend Authentication

Frontend authentication now supports:

- Login through `POST /users/login`
- JWT access-token storage in `localStorage`
- Authenticated requests through `authenticatedFetch`
- Current-user retrieval through `GET /users/me`
- Display of the authenticated user's email and admin status

Runtime authentication was verified successfully in the browser.

### Step 41 — Frontend Product Details

The frontend supports navigation from the product list to a dedicated product detail page.

```text
Products Page
    ↓
View Product
    ↓
/products/:productId
    ↓
GET /products/{product_id}
    ↓
Product Details Page
```

The Product Details page loads the product using the route parameter, handles loading and error states, and displays title, description, price, and stock status.

The backend endpoint returns `404` when the requested product does not exist.

Product Details was verified successfully in the browser using `/products/1`.

### Step 42 — Frontend Cart

The frontend now provides an authenticated shopping cart flow.

```text
Product Details
      ↓
Add to Cart
      ↓
POST /cart/
      ↓
Cart Page
      ↓
GET /cart/
      ↓
Cart Items
```

Implemented capabilities:

- Retrieve the current user's cart through `GET /cart/`
- Add a product through `POST /cart/`
- Increase the quantity of an existing cart item
- Remove an item through `DELETE /cart/{item_id}`
- Select a quantity on the Product Details page
- Prevent selecting a quantity above displayed product stock in the UI
- Calculate cart total as `price × quantity`

The backend remains responsible for authoritative product existence and stock validation. The frontend quantity limit is a user-experience safeguard, not a security boundary.

The Cart flow was runtime-verified in the browser, including adding a product, displaying quantity and total, and removing the item.

Frontend validation:

```text
npm run build → green
npm run lint  → green
```
### Steps 43–48 — Frontend Orders & Payment

The frontend now supports authenticated order management and payment flows.

Implemented capabilities:

- List the current user's orders through `GET /orders/`
- Cancel pending orders
- Process payments through `POST /payment/process`
- Use an idempotency key for frontend payment requests
- Retrieve payment details through `GET /payment/orders/{order_id}`
- Display payment status, amount, transaction ID, creation time, paid time, and refunded time
- Refund paid orders
- Keep Order and Payment states consistent after refund

The refund flow now results in:

```text
Payment status → refunded
Order status   → cancelled
```
Runtime verification completed successfully in the browser.

## Testing

Run the backend suite:

```bash
docker compose exec web pytest -q
```

Latest verified result:

```text
56 passed
```

The test suite uses a dedicated PostgreSQL database named `ecommerce_db_test`, keeping automated test data separate from the development database.

Run frontend checks:

```bash
cd frontend
npm run build
npm run lint
```

Both commands were verified green locally.

GitHub Actions now verifies Docker Compose startup, database migrations, the backend Pytest suite, frontend dependency installation, frontend lint, and frontend production build.

## Current Development Progress

```text
Step 1–25  — Core platform milestones                         ✅
Step 30    — Persistent Payment Records                       ✅
Step 31    — Payment Refund Flow                              ✅
Step 32    — Payment Idempotency                              ✅
Step 33    — Payment Audit History                            ✅
Step 34    — Rich Payment Audit Metadata                      ✅
Step 35    — Payment Webhooks                                 ✅
Step 36    — Webhook Delivery & Retry Infrastructure           ✅
Step 37    — Security & API Hardening                          ✅
Step 38    — Observability + Grafana Dashboard                 ✅
Step 39    — Frontend Foundation + Product Integration          ✅
Step 40    — Frontend Authentication                            ✅
Step 41    — Frontend Product Details                           ✅
Step 42    — Frontend Cart                                     ✅
Step 48    — Frontend Orders + Payment                         ✅
Step 49    — Frontend CI Validation                            ✅

```

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

Steps 37–42 add no database migration.

## Development Workflow

```text
Inspect → Implement → Test → Update documentation → Review Git diff → Commit → Push → Verify CI
```

## Project Status

Latest documented milestone:

Step 49 — Frontend CI Validation

Orders + Payment + CI

```text
56 passed
```

Latest verified frontend result:

```text
build: green
lint: green
```

The payment provider remains simulated. The platform now has a working React frontend connected to the FastAPI backend, including product browsing, authentication, cart, checkout, order management, payment processing, payment details, refunds, and frontend CI validation.

## Documentation

- `PROJECT_STATE.md`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
