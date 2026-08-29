# PROJECT_STATE

## Objective
Build a production-oriented e-commerce backend with FastAPI, PostgreSQL, Redis, SQLAlchemy, JWT, Alembic, Docker, Pytest, GitHub Actions, SlowAPI, Celery, inventory management, payment persistence, refunds, payment idempotency, audit history, rich audit metadata, payment webhooks, webhook delivery/retry infrastructure, security hardening, observability, and production-readiness practices.

## Current Architecture

```text
Client
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
  │     └── Request ID / correlation
  └── Background Tasks

PostgreSQL ← application data
Redis      ← cache / rate limiting / Celery broker/backend
Prometheus ← API metrics scraping
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

## Implemented Features

### Orders

```text
pending → paid → processing → shipped → delivered
   |
   └────────────→ cancelled
```

Checkout performs stock reservation, creates Order/OrderItems/Shipping transactionally, and rolls back on failure.

### Payment — Step 30

Persistent `Payment` entity with `order_id`, `amount`, `status`, `transaction_id`, `created_at`, `paid_at`, and `refunded_at`.

### Refund — Step 31

`POST /payment/{order_id}/refund` validates ownership, Payment existence, paid state, and duplicate-refund protection. Successful refunds set `status=refunded` and `refunded_at`.

### Idempotency — Step 32

`Payment` stores `idempotency_key` with database uniqueness:

```text
UNIQUE(idempotency_key)
constraint: uq_payments_idempotency_key
```

`POST /payment/process` accepts an optional idempotency key:

- Same key + same order → existing Payment response is returned.
- Same key + different order → HTTP 409.
- No key → existing payment flow remains supported.

Migration:

```text
aea3438feb25_add_payment_idempotency_key.py
```

### Payment Audit History — Step 33

A dedicated `PaymentEvent` entity and `payment_events` table record important Payment state changes as append-only audit records.

Fields:

```text
id
payment_id
event_type
status
created_at
actor_user_id
metadata
event_id
```

Current event types include:

```text
payment_created
payment_refunded
webhook_paid
webhook_refunded
```

Behavior:

- Successful payment creates one `payment_created` event.
- Successful refund creates one `payment_refunded` event.
- Replaying the same idempotent payment request does not create another event.
- Webhook delivery can create an immutable webhook audit event.
- Events are linked to Payment with a one-to-many relationship and cascade on Payment deletion.

Migration:

```text
e124ed32b079_add_payment_events_table.py
```

### Rich Payment Audit Metadata — Step 34

`PaymentEvent` records the authenticated actor and structured event context.

Additional fields:

```text
actor_user_id
metadata (JSON)
```

`actor_user_id` is a nullable foreign key to `users.id`. Metadata stores contextual information such as order ID, amount, transaction ID, refund timestamp, webhook event ID, and source.

Migration:

```text
2a408bf8badb_add_payment_audit_metadata.py
```

### Payment Webhooks — Step 35

A provider callback endpoint is exposed at:

```text
POST /payment/webhook
```

Webhook payload:

```text
transaction_id
status
event_id
```

Security:

- HMAC-SHA256 signature validation using `PAYMENT_WEBHOOK_SECRET`.
- Requests with an invalid signature return HTTP 401.

Processing rules:

- Unknown transaction IDs return HTTP 404.
- Unsupported statuses return HTTP 400.
- `paid` updates Payment and Order to paid and records `paid_at` when needed.
- `refunded` updates Payment and Order to refunded/cancelled and records `refunded_at` when needed.
- Each processed webhook creates a `PaymentEvent` with the webhook `event_id` and source metadata.
- Repeated delivery with the same `event_id` is treated as already processed and does not create a duplicate event.

Migration:

```text
e3e6a6bd5e42_add_payment_webhook_event_id.py
```

### Webhook Delivery & Retry Infrastructure — Step 36

Webhook processing is moved to Celery and Redis.

Flow:

```text
Webhook request
      ↓
HMAC validation
      ↓
event_id duplicate check
      ↓
persist webhook event
      ↓
Celery queue
      ↓
process_payment_webhook
      ↓
update Payment / Order
      ↓
commit
```

Celery task:

```text
app.tasks.payment_tasks.process_payment_webhook
```

Redis configuration:

```text
redis://redis:6379/0
```

Retry policy:

- Only transient `ConnectionError` failures are retried.
- Maximum retries: 3.
- Retry uses backoff.
- Permanent domain errors are not retried as transient errors.

Webhook processing status is recorded in `PaymentEvent.metadata`:

```text
processing
processed
failed_after_retries
```

Worker verification confirmed the task is registered, receives jobs from Redis, processes webhook events, and performs the configured retry cycle for transient failures.

### Security & API Hardening — Step 37

Security hardening was applied across authentication, password validation, HTTP responses, CORS, and application configuration.

JWT controls:

```text
exp
iat
type=access
```

Password policy:

```text
minimum length = 8
```

Security response headers include:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy
```

CORS is configuration-driven through `CORS_ORIGINS` and explicitly restricts allowed origins, methods, and headers.

Security-sensitive configuration is validated during startup:

```text
SECRET_KEY
PAYMENT_WEBHOOK_SECRET
```

Unhandled exceptions return a generic HTTP 500 response without exposing internal exception details.

### Observability — Step 38

The application now exposes Prometheus-compatible HTTP metrics, centralized request logging, and request correlation IDs.

Metrics:

```text
http_requests_total
http_request_duration_seconds
```

Metrics are exposed at:

```text
GET /metrics
```

Prometheus configuration:

```text
prometheus.yml
```

Prometheus scrapes `web:8000/metrics` every 5 seconds using the `ecommerce_api` job.

Request logs contain:

```text
method
path
status
request_id
duration_ms
```

Logging severity:

```text
2xx/3xx → INFO
4xx     → WARNING
5xx     → ERROR
```

`X-Request-ID` is preserved when supplied by the client and generated as a UUID when absent. It is returned in the response and included in application logs.

Unhandled exceptions are logged with the request ID while the client receives a generic 500 response.

## Testing

Latest full-suite verification:

```text
56 passed
```

Command:

```bash
docker compose exec web pytest -q
```

Step 35 coverage includes valid/invalid HMAC signatures, unknown payments, unsupported statuses, successful webhook handling, and duplicate webhook protection.

Step 36 coverage includes Celery task registration, Redis-backed dispatch, real worker execution, retry handling, maximum retry enforcement, processing-state tracking, and retry-exhaustion tracking.

Step 37 coverage includes JWT access-token claims and type validation, minimum password length, security response headers, configured/rejected CORS origins, startup security validation, and safe unhandled-exception handling.

Step 38 coverage includes Prometheus metrics exposure, request latency tracking, request ID propagation/generation, 4xx and 5xx observability, and exception log correlation.

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

Step 38 adds no database migration.

## Repository Status

Latest documented implementation:

```text
Step 38 — Observability
```

Latest verified local suite before documentation sync:

```text
56 passed
git diff --check → clean
```

The Step 38 application changes are implemented locally and are ready for the next application-code commit/push.

## Current Known Good State

```text
Step 36 — Webhook Delivery & Retry        COMPLETED
Step 37 — Security & API Hardening        COMPLETED
Step 38 — Observability                   IMPLEMENTED
Tests                                     56 passed
Alembic head                              e3e6a6bd5e42
```

## Major Lessons Learned

- Alembic is the authoritative schema-management mechanism.
- Database uniqueness is required in addition to application checks for payment idempotency.
- Idempotency must distinguish replaying the same command from reusing a key for another order.
- Payment/refund ownership must be enforced before state changes.
- Audit history should be append-only and stored separately from mutable Payment state.
- Duplicate idempotent requests must not create duplicate audit events.
- Audit actors and structured metadata make payment history operationally traceable.
- Webhooks require signature verification and their own idempotency mechanism.
- Asynchronous webhook processing should be separated from the HTTP request path.
- Only transient infrastructure failures should trigger automatic retries.
- Retry exhaustion should leave an operationally visible state.
- JWT tokens should carry explicit access-token semantics.
- Password validation should enforce a minimum security baseline.
- CORS should be explicitly configured instead of using wildcard origins.
- Security headers should be added at the application boundary.
- Sensitive configuration should be validated during startup.
- Unexpected application errors should not expose internal details to clients.
- Prometheus metrics provide machine-readable signals for request rate and latency.
- Request IDs make logs traceable across individual HTTP requests.
- Error-level logging should retain correlation context without exposing sensitive details to clients.
- Payment and refund remain mock provider operations.

## Pending Work

- Commit and push Step 38 application implementation plus updated documentation.
- Verify GitHub Actions is green for the final Step 38 remote state.

## Future Enhancements

- Real payment gateway integration
- Provider webhook delivery/retry infrastructure beyond the local Celery simulation
- Richer payment audit event types and correlation IDs
- Structured JSON logging
- Distributed tracing
- API versioning
- Advanced inventory policies
- Production alerting and SLO-based monitoring

## Next Recommended Step

After Step 38 application-code commit and CI verification, continue to the next platform milestone.

## Notes For Future Sessions

Start with:

```bash
git status --short
git log -1 --oneline
docker compose exec web pytest -q
docker compose exec web alembic current
```
