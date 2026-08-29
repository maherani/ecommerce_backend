# E-Commerce Backend

Production-oriented e-commerce backend built with FastAPI, PostgreSQL, Redis, SQLAlchemy, JWT authentication, Alembic, Docker, Pytest, GitHub Actions, SlowAPI, and Celery.

## Architecture

```text
Client / Frontend
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
       +---- Background Tasks
       |
       +---- PostgreSQL
       +---- Redis
```

Docker Compose services: `db`, `redis`, `web`, `celery_worker`.

## Payment

### Step 30 — Persistent Payment Records

`POST /payment/process` persists a Payment record, generates a unique transaction ID, records `paid_at`, and changes the order from `pending` to `paid`.

Migration:

```text
cff58edd10a9_add_payments_table.py
```

### Step 31 — Payment Refund

```text
POST /payment/{order_id}/refund
```

Only the authenticated order owner can refund. Payment and order must still be `paid`; duplicate refunds are rejected. `refunded_at` is recorded and the original transaction ID is preserved.

### Step 32 — Payment Idempotency

`POST /payment/process` accepts an optional `idempotency_key`.

The key is persisted on `payments.idempotency_key` with a unique database constraint:

```text
uq_payments_idempotency_key
```

Behavior:

- Same key + same order: returns the existing Payment result without creating another Payment.
- Same key + different order: returns HTTP `409`.
- Requests without a key remain supported.

Migration:

```text
aea3438feb25_add_payment_idempotency_key.py
```

### Step 33 — Payment Audit History

A dedicated `payment_events` table records important Payment state changes without overwriting the Payment record.

The `PaymentEvent` entity stores:

```text
payment_id
event_type
status
created_at
actor_user_id
metadata
event_id
```

Current events include payment creation, refund, and webhook events. Duplicate idempotent payment requests and duplicate webhook deliveries do not create duplicate audit events.

Migration:

```text
e124ed32b079_add_payment_events_table.py
```

### Step 34 — Rich Payment Audit Metadata

Payment events record the actor responsible for the event and structured JSON metadata. User-triggered payment/refund events store `actor_user_id`; webhook events can use a null actor.

Metadata can include order ID, amount, transaction ID, refund timestamp, event ID, and event source.

Migration:

```text
2a408bf8badb_add_payment_audit_metadata.py
```

### Step 35 — Payment Webhooks

A provider callback endpoint is available at:

```text
POST /payment/webhook
```

Webhook payload:

```text
transaction_id
status
event_id
```

Webhook security and behavior:

- HMAC-SHA256 signature validation using `PAYMENT_WEBHOOK_SECRET`.
- Unknown transactions return HTTP `404`.
- Unsupported statuses return HTTP `400`.
- Supported `paid` and `refunded` states update Payment and Order state.
- Each processed webhook creates a `PaymentEvent` with `event_id` and source metadata.
- Repeated delivery with the same `event_id` returns `Webhook already processed` and does not create another audit event.

Migration:

```text
e3e6a6bd5e42_add_payment_webhook_event_id.py
```
### Step 36 — Webhook Delivery & Retry Infrastructure

Webhook processing is asynchronous and is handled by Celery using Redis as the broker/backend.

Processing flow:

```text
External Provider
       |
       v
POST /payment/webhook
       |
       v
Validate HMAC + event_id
       |
       v
Persist webhook event
       |
       v
Celery task
       |
       v
Process Payment / Order
       |
       v
Commit

Retry behavior:

Transient ConnectionError failures are retried.
Maximum retries: 3.
Retry uses backoff.
Permanent domain errors such as missing webhook events, missing payments, or unsupported statuses are not treated as transient retry conditions.

Webhook processing status is stored in PaymentEvent.metadata:

processing
processed
failed_after_retries

Celery task:

app.tasks.payment_tasks.process_payment_webhook

Redis broker/backend:

redis://redis:6379/0

The test suite verifies asynchronous dispatch, retry handling, and retry exhaustion tracking.
```
### Step 37 — Security & API Hardening

Security hardening was applied across authentication, password validation, HTTP responses, CORS, and application configuration.

Implemented controls:

- JWT access tokens now contain `exp`, `iat`, and `type=access`.
- Authenticated requests require a valid access-token type.
- User registration requires a password with a minimum length of 8 characters.
- Security response headers are added:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy`
- CORS origins are configuration-driven through `CORS_ORIGINS`.
- CORS methods and headers are explicitly restricted.
- Security-sensitive settings are validated during application startup.
- Unhandled exceptions return a generic HTTP 500 response without exposing internal error details.

The security changes are covered by automated regression tests.


## Testing

Run the full suite:

```bash
docker compose exec web pytest -q
```

```text
Latest verified result:

50 passed
```

Coverage includes payment persistence, refunds, idempotency, audit history, rich audit metadata, webhook signature validation, webhook error handling, webhook state transitions, duplicate webhook protection, JWT hardening, password validation, security headers, CORS restrictions, security-setting validation, and safe unhandled-exception handling.

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
Step 22 — Atomic Stock Reservation              ✅
Step 23 — Order Cancellation & Stock Restoration ✅
Step 24 — Order Lifecycle & Admin Management    ✅
Step 25 — Shipping & Delivery Management        ✅
Step 30 — Persistent Payment Records            ✅
Step 31 — Payment Refund Flow                   ✅
Step 32 — Payment Idempotency                   ✅
Step 33 — Payment Audit History                 ✅
Step 34 — Rich Payment Audit Metadata           ✅
Step 35 — Payment Webhooks                      ✅
Step 36 — Webhook Delivery & Retry Infrastructure ✅
Step 37 — Security & API Hardening              ✅
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

## Development Workflow

```text
Inspect → Implement → Test → Update documentation → Review Git diff → Commit → Push → Verify CI
```

## Project Status

Latest implemented milestone:

```text
Step 37 — Security & API Hardening
```

Latest verified local test result:

```text
50 passed

```

Payment provider integration remains simulated. Step 36 provides asynchronous webhook processing and retry handling, while Step 37 adds security hardening across JWT authentication, password validation, HTTP security headers, CORS, startup configuration validation, and safe exception handling.
## Documentation

- `PROJECT_STATE.md`
- `docs/ARCHITECTURE.md`
