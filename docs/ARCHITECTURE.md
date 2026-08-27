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
  └── Background Tasks
      └── Celery Worker

PostgreSQL ← primary database
Redis      ← cache / rate limiting / Celery broker/backend
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

Celery task:

app.tasks.payment_tasks.process_payment_webhook

Redis:

redis://redis:6379/0

Retry policy:

ConnectionError
      ↓
retry #1
      ↓
retry #2
      ↓
retry #3
      ↓
failed_after_retries

Only transient ConnectionError failures are retried.

Permanent domain errors such as:

missing webhook event
missing payment
unsupported status

are not automatically retried.

Processing state is stored in PaymentEvent.metadata:

processing
processed
failed_after_retries

The webhook event_id remains unique, preventing duplicate delivery from queueing duplicate processing.

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

## 7. Testing and CI

Latest verified local suite:

```text
43 passed
```

Coverage includes valid/invalid webhook signatures, unknown payments, unsupported statuses, successful webhook handling, and duplicate webhook protection.
Celery task registration
Redis-backed dispatch
real worker execution
transient retry handling
maximum retry count
processing state tracking
retry exhaustion tracking

CI performs Docker Compose startup, PostgreSQL readiness, `alembic upgrade head`, and Pytest.

## 8. Current Status

```text
Step 36 — Webhook Delivery & Retry Infrastructure

```
43 passed
Local implementation commit:

```text
1a38376 feat: add payment webhooks
```
