# Architecture

## 1. System Overview

```text
Client
  ↓
FastAPI
  ├── User
  ├── Product / Category
  ├── Cart
  ├── Order / OrderItem
  │     ├── Shipping (1:1)
  │     └── Payment (1:1)
  │             └── PaymentEvent (1:N)
  ├── Rate Limiting
  ├── Observability
  │     ├── Prometheus metrics
  │     ├── Request logging
  │     └── Request ID / correlation
  └── Background Tasks
      └── Celery Worker

PostgreSQL ← primary database
Redis      ← cache / rate limiting / Celery broker/backend
Prometheus ← API metrics scraping
```

## 2. Domain Relationships

```text
User
 |
 +----< Order
          |
          +----< OrderItem >---- Product
          |
          +---- Shipping   (1:1)
          |
          +---- Payment    (1:1)
                     |
                     +----< PaymentEvent
```

Each Payment can have multiple immutable PaymentEvent records representing significant state changes.

## 3. Payment Processing

### Step 30

```text
pending Order
   ↓
POST /payment/process
   ↓
verify ownership
   ↓
create Payment(status=paid)
   ↓
transaction_id + paid_at
   ↓
Order.status = paid
```

### Step 31 — Refund

```text
paid Order
   ↓
POST /payment/{order_id}/refund
   ↓
validate ownership + paid state
   ↓
Payment.status = refunded
   ↓
refunded_at
```

Refund is currently a mock domain operation.

### Step 32 — Idempotency

```text
POST /payment/process
        |
        +---- optional idempotency_key
        |
        v
lookup existing Payment by key
        |
        +---- same order → return existing result
        |
        +---- different order → HTTP 409
        |
        v
create Payment with key
```

The `payments.idempotency_key` column is nullable for backward compatibility and has the unique constraint `uq_payments_idempotency_key`.

### Step 33 — Payment Audit History

```text
Payment created
     ↓
PaymentEvent(payment_created)

Payment refunded
     ↓
PaymentEvent(payment_refunded)
```

`PaymentEvent` stores the immutable audit record separately from mutable Payment state.

### Step 34 — Rich Payment Audit Metadata

```text
PaymentEvent
    |
    +---- actor_user_id → users.id
    |
    +---- event_type
    |
    +---- status
    |
    +---- metadata (JSON)
    |
    +---- created_at
```

The authenticated user is stored as the actor for user-generated payment/refund events. Structured JSON metadata records contextual information such as order ID, amount, transaction ID, and refund timestamp.

### Step 35 — Payment Webhooks

```text
External Provider
       ↓
POST /payment/webhook
       ↓
verify HMAC-SHA256 signature
       ↓
check event_id
       |
       +---- already processed → return existing result
       |
       v
lookup Payment by transaction_id
       ↓
validate webhook status
       ↓
persist webhook PaymentEvent
       ↓
queue Celery task
```

Webhook payload:

```text
transaction_id
status
event_id
```

Security:

- `PAYMENT_WEBHOOK_SECRET` is used to calculate the HMAC-SHA256 digest.
- Signature comparison uses a constant-time comparison.
- Invalid signatures are rejected with HTTP 401.

Supported state changes:

```text
paid     → Payment.status=paid, Order.status=paid
refunded → Payment.status=refunded, Order.status=cancelled
```

Webhook audit records contain `event_id` and identify their source as `payment_webhook`. A unique `event_id` prevents duplicate webhook processing.

The HTTP request validates and persists the webhook event. Payment and Order state changes are handled asynchronously by the Step 36 Celery worker.

### Step 36 — Webhook Delivery & Retry Infrastructure

```text
Webhook HTTP request
       ↓
HMAC validation
       ↓
event_id duplicate check
       ↓
Payment lookup
       ↓
status validation
       ↓
persist PaymentEvent
       ↓
Celery / Redis queue
       ↓
process_payment_webhook
       ↓
load webhook event
       ↓
process Payment / Order
       ↓
commit
```

Celery task:

```text
app.tasks.payment_tasks.process_payment_webhook
```

Redis:

```text
redis://redis:6379/0
```

Retry policy:

```text
ConnectionError
      ↓
retry #1
      ↓
retry #2
      ↓
retry #3
      ↓
failed_after_retries
```

Only transient `ConnectionError` failures are retried.

Permanent domain errors such as missing webhook events, missing payments, or unsupported statuses are not automatically retried.

Processing state is stored in `PaymentEvent.metadata`:

```text
processing
processed
failed_after_retries
```

The webhook `event_id` remains unique, preventing duplicate delivery from queueing duplicate processing.

### Step 37 — Security & API Hardening

```text
Client
  ↓
FastAPI
  ↓
Security Middleware
  ├── Security Headers
  └── CORS restrictions
  ↓
Authentication
  ├── JWT signature validation
  ├── exp validation
  └── type=access validation
  ↓
Application routes
```

Security controls:

```text
JWT
  ├── exp
  ├── iat
  └── type=access

Password
  └── minimum length = 8

HTTP headers
  ├── X-Content-Type-Options
  ├── X-Frame-Options
  ├── Referrer-Policy
  └── Permissions-Policy

CORS
  ├── configured origins
  ├── restricted methods
  └── restricted headers
```

Security-sensitive configuration is validated during startup:

```text
SECRET_KEY
PAYMENT_WEBHOOK_SECRET
```

Unhandled exceptions are converted to a generic HTTP 500 response without exposing internal exception details.

Step 37 adds no database migration; it hardens application security and request handling around the existing schema.

### Step 38 — Observability

```text
Client
  ↓
FastAPI
  ↓
MetricsMiddleware
  ├── request_id generation/preservation
  ├── request duration measurement
  ├── HTTP status classification
  └── Prometheus metrics
        ↓
      /metrics
        ↓
   Prometheus
```

Prometheus metrics:

```text
http_requests_total
http_request_duration_seconds
```

`GET /metrics` exposes Prometheus-compatible metrics. The Prometheus service scrapes `web:8000/metrics` every 5 seconds using the `ecommerce_api` job.

Request logging records:

```text
method
path
status
request_id
duration_ms
```

Log severity is based on response status:

```text
2xx/3xx → INFO
4xx     → WARNING
5xx     → ERROR
```

Unhandled exceptions are logged with the request correlation ID while the client receives a generic HTTP 500 response.

`X-Request-ID` is preserved when supplied by the client and generated as a UUID when absent. It is returned in the response header and included in application logs.

5xx exceptions are also recorded in the request metrics with `status=500` before the exception is re-raised to the global exception handler.

## 4. Checkout Transaction

```text
Cart
 ↓
Lock Product rows
 ↓
Validate stock
 ↓
Decrease stock
 ↓
Create Order
 ↓
Create OrderItems
 ↓
Create Shipping
 ↓
Clear Cart
 ↓
Commit
```

Failed checkout rolls back the transaction.

## 5. Authentication / Authorization

JWT authentication protects user-specific payment and refund operations. Ownership is checked at the Order query level before Payment state changes. Webhooks are provider-authenticated by HMAC rather than user JWT.

## 6. Persistence and Migrations

Alembic is the authoritative schema-management mechanism.

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

Step 35 adds a unique `event_id` to `payment_events` so provider webhook delivery can be handled idempotently.

Step 38 adds no database migration.

## 7. Testing and CI

Latest verified local suite:

```text
56 passed
```

Coverage includes:

```text
Payment persistence and refunds
Payment idempotency and audit history
Webhook signature validation and duplicate protection
Celery task registration and Redis-backed dispatch
Transient retry handling and retry exhaustion tracking
JWT access-token claims and type validation
Password minimum length validation
Security response headers and CORS restrictions
Startup security-setting validation
Safe unhandled-exception responses
Prometheus metrics exposure and request latency
Request ID propagation and generation
4xx and 5xx observability
Exception logging correlation
```

CI performs Docker Compose startup, PostgreSQL readiness, `alembic upgrade head`, and Pytest.

## 8. Current Status

```text
Step 38 — Observability

56 passed

Step 38 application changes are implemented locally and the documentation has been synchronized to the latest verified state.
```
