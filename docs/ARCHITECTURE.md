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
  │     └── Payment  (1:1)
  │             └── PaymentEvent (1:N)
  ├── Rate Limiting
  └── Background Tasks

PostgreSQL ← primary database
Redis      ← cache / rate limiting / Celery
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

`PaymentEvent` fields:

```text
payment_id
event_type
status
created_at
```

Audit events are stored separately from mutable Payment state. Replaying the same idempotent payment request returns the existing payment and does not create another audit event.

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

The authenticated user is stored in `actor_user_id` for payment and refund events. Structured JSON metadata captures contextual information such as order ID, payment amount, transaction ID, and refund timestamp.

Payment event creation now follows this pattern:

```text
authenticated request
        ↓
state change
        ↓
create PaymentEvent
        ├── actor_user_id
        ├── event_type
        ├── status
        └── metadata
        ↓
commit
```

The actor foreign key is nullable for compatibility with non-user-generated events that may be introduced later.

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

JWT authentication protects user-specific payment and refund operations. Ownership is checked at the Order query level before Payment state changes. Audit events record the authenticated actor responsible for those changes.

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
```

Step 34 adds `actor_user_id` with a foreign key to `users.id` and a JSON `metadata` column to `payment_events`.

## 7. Testing and CI

Latest verified local suite:

```text
37 passed
```

CI performs Docker Compose startup, PostgreSQL readiness, `alembic upgrade head`, and Pytest.

Step 34 tests cover actor attribution and structured metadata for payment and refund audit events.

## 8. Current Status

```text
Step 34 — Rich Payment Audit Metadata
```

Local implementation commit:

```text
bee233b feat: enrich payment audit metadata
```
