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
       +---- Observability
       |       +---- Prometheus metrics
       |       +---- Request logging
       |       +---- Request ID / correlation
       |       +---- Grafana dashboards
       +---- Background Tasks
       |
       +---- PostgreSQL
       +---- Redis
```

Docker Compose services: `db`, `redis`, `web`, `celery_worker`, `prometheus`, and `grafana`.

## Payment

### Step 30 — Persistent Payment Records
`POST /payment/process` persists Payment state, creates a unique transaction ID, records `paid_at`, and changes a pending order to paid.

### Step 31 — Payment Refund
`POST /payment/{order_id}/refund` validates ownership and paid state, prevents duplicate refunds, records `refunded_at`, and preserves the original transaction ID. The provider operation remains simulated.

### Step 32 — Payment Idempotency
`POST /payment/process` accepts an optional `idempotency_key`, persisted with the unique constraint `uq_payments_idempotency_key`. Replaying the same key for the same order returns the existing result; using it for another order returns HTTP 409.

### Step 33 — Payment Audit History
The `payment_events` table stores immutable Payment state-change events, including payment creation, refunds, and webhook events.

### Step 34 — Rich Payment Audit Metadata
Payment events include `actor_user_id` and structured JSON metadata containing contextual information such as order ID, amount, transaction ID, refund timestamp, webhook event ID, and source.

### Step 35 — Payment Webhooks
`POST /payment/webhook` validates an HMAC-SHA256 signature, checks `event_id` idempotency, validates the transaction and status, records an audit event, and supports `paid` and `refunded` state changes.

### Step 36 — Webhook Delivery & Retry Infrastructure
Webhook state processing is asynchronous through Celery and Redis. Transient `ConnectionError` failures are retried up to 3 times with backoff; permanent domain errors are not treated as transient failures. Processing state is stored in `PaymentEvent.metadata`.

### Step 37 — Security & API Hardening
JWT access-token claims, password minimum length, security response headers, configuration-driven CORS, startup security validation, and safe generic 500 responses are implemented.

### Step 38 — Observability
The API exposes:

```text
http_requests_total
http_request_duration_seconds
```

Metrics are available at `GET /metrics`. Prometheus uses `prometheus.yml` and scrapes `web:8000/metrics` every 5 seconds through the `ecommerce_api` job.

Request logs contain:

```text
method
path
status
request_id
duration_ms
```

`X-Request-ID` is preserved when supplied and generated as a UUID when absent. It is returned in the response and included in logs. HTTP 5xx responses are also represented in request metrics.

### Grafana Dashboard

Grafana is deployed as a Docker Compose service on port `3000`, uses the persistent `grafana_data` volume, and reads Prometheus metrics from the internal Compose network.

Current dashboard:

```text
Dashboard: Dashbourd 1
```

Current panels:

| Panel | Type | PromQL |
|---|---|---|
| API Request Rate | Time series | `rate(http_requests_total[1m])` |
| API Request Latency (P95) | Time series | `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))` |
| API Error Rate | Time series | `sum(rate(http_requests_total{status=~"4..|5.."}[5m]))` |
| Requests by Endpoint | Time series | `sum by (endpoint) (rate(http_requests_total[5m]))` |
| HTTP Requests by Status | Time series | `sum by (status) (rate(http_requests_total[5m]))` |

This Grafana dashboard is the visualization layer for the Step 38 Prometheus observability foundation.

## Testing

Run the full suite:

```bash
docker compose exec web pytest -q
```

Latest verified local result:

```text
56 passed
```

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

Step 38 adds no database migration.

## Development Workflow

```text
Inspect → Implement → Test → Update documentation → Review Git diff → Commit → Push → Verify CI
```

## Project Status

Latest documented milestone:

```text
Step 38 — Observability + Grafana Dashboard
```

Latest verified local test result:

```text
56 passed
```

The payment provider remains simulated. The platform now has security hardening from Step 37 and an observability stack based on Prometheus metrics, request logging, request correlation IDs, and Grafana visualization.

## Documentation

- `PROJECT_STATE.md`
- `docs/ARCHITECTURE.md`
