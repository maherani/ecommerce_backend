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
```

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

The `payments.idempotency_key` column is nullable for backward compatibility and has a unique constraint:

```text
uq_payments_idempotency_key
```

This provides database-level protection against duplicate key usage in addition to the application-level lookup.

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

JWT authentication protects user-specific payment and refund operations. Ownership is checked at the Order query level before Payment state changes.

## 6. Persistence and Migrations

Alembic is the authoritative schema-management mechanism.

```text
40f98fd888bb_add_shipping_table.py
                ↓
cff58edd10a9_add_payments_table.py
                ↓
aea3438feb25_add_payment_idempotency_key.py
```

Step 32 adds only the `idempotency_key` column and its unique constraint; no new Payment table is introduced.

## 7. Testing and CI

Latest verified local suite:

```text
35 passed
```

CI performs Docker Compose startup, PostgreSQL readiness, `alembic upgrade head`, and Pytest.

## 8. Current Status

```text
Step 32 — Payment Idempotency
```

Local implementation commit:

```text
7035c30 feat: add payment idempotency
```
