# E-Commerce Backend

Production-oriented e-commerce backend built with FastAPI, PostgreSQL, Redis, SQLAlchemy, JWT authentication, Alembic, Docker, Pytest, GitHub Actions, SlowAPI, and Celery.

## Architecture

```text
Client / Frontend
       |
       v
    FastAPI (web)
       |
       +---- User
       +---- Product / Category
       +---- Cart
       +---- Order / OrderItem
       +---- Shipping (1:1)
       +---- Payment (1:1)
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

## Testing

Run the full suite:

```bash
docker compose exec web pytest -q
```

Latest verified result:

```text
35 passed
```

Coverage includes payment persistence, duplicate-payment protection, refunds, refund authorization, idempotency-key replay handling, and cross-order idempotency-key protection.

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
Step 22 — Inventory & Atomic Stock Reservation  ✅
Step 23 — Order Cancellation & Stock Restoration ✅
Step 24 — Order Lifecycle & Admin Management    ✅
Step 25 — Shipping & Delivery Management        ✅
Step 30 — Persistent Payment Records            ✅
Step 31 — Payment Refund Flow                   ✅
Step 32 — Payment Idempotency                   ✅
```

## Database Migration Chain

```text
40f98fd888bb_add_shipping_table.py
                ↓
cff58edd10a9_add_payments_table.py
                ↓
aea3438feb25_add_payment_idempotency_key.py
```

## Development Workflow

```text
Inspect → Implement → Test → Update documentation → Review Git diff → Commit → Push → Verify CI
```

## Project Status

Latest implemented milestone:

```text
Step 32 — Payment Idempotency
```

Latest verified local test result:

```text
35 passed
```

Idempotency is currently implemented at the domain/database level; real payment-provider integration remains future work.

## Documentation

- `PROJECT_STATE.md`
- `docs/ARCHITECTURE.md`
