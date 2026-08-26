# Architecture

## 1. System Overview

The application is a Dockerized FastAPI e-commerce backend with PostgreSQL as the primary relational database and Redis as shared infrastructure for caching, rate limiting, and Celery.

```text
Client / Frontend
       |
       v
    FastAPI (web)
       |
       +-------------------+
       |                   |
       v                   v
   Domain Modules       Infrastructure
       |                   |
       |                   +---- PostgreSQL
       |                   +---- Redis
       |
       +---- User
       +---- Product / Category
       +---- Cart
       +---- Order / OrderItem
       +---- Shipping
       +---- Payment

FastAPI registration
       |
       v
Celery task -> Redis broker/result backend -> celery_worker
```

## 2. Docker Compose

```text
db ------------- PostgreSQL
redis ---------- Redis
web ------------ FastAPI
celery_worker -- Celery Worker
```

The `web` and `celery_worker` services share the application image and internal Docker network.

## 3. Domain Relationships

```text
User
 |
 +----< Order
          |
          +----< OrderItem >---- Product
          |
          +----  Shipping   (1:1)
          |
          +----  Payment    (1:1)
```

### Shipping

Each checkout creates one Shipping record for the new Order.

```text
Order 1 -------- 1 Shipping
```

### Payment

Each Order can have at most one Payment record.

```text
Order 1 -------- 1 Payment
```

Payment stores:

```text
order_id
amount
status
transaction_id
created_at
paid_at
refunded_at
```

Database constraints enforce the Payment foreign key and uniqueness of `order_id` and `transaction_id`.

## 4. Order Lifecycle

```text
pending → paid → processing → shipped → delivered
   |
   └────────────→ cancelled
```

Rules are centralized in the Order module.

- `pending` can become `paid` or `cancelled`.
- `paid` can become `processing`.
- `processing` can become `shipped`.
- `shipped` can become `delivered`.
- `delivered` and `cancelled` are terminal states.

Admin status endpoint:

```text
PATCH /orders/{order_id}/status
```

## 5. Checkout Transaction

Checkout is transactional and performs inventory reservation and domain-object creation together.

```text
Cart
  |
  v
Lock Product rows
  |
  v
Validate stock
  |
  v
Decrease stock
  |
  v
Create Order
  |
  v
Create OrderItems
  |
  v
Create Shipping
  |
  v
Clear Cart
  |
  v
Commit
```

If checkout fails, the transaction is rolled back so that an Order or Shipping record is not left behind and reserved inventory is not incorrectly consumed.

## 6. Payment Processing

Step 30 introduced persistent Payment storage.

```text
pending Order
     |
     v
POST /payment/process
     |
     +---- verify authenticated ownership
     +---- verify order.status == pending
     +---- reject existing payment
     +---- generate transaction_id
     +---- create Payment(status=paid)
     +---- set paid_at
     +---- set Order.status = paid
     +---- commit
     |
     v
PaymentResponse
```

The payment gateway is intentionally a mock.

## 7. Refund Processing — Step 31

Refund is implemented as a domain-level state transition on the existing Payment record; no new database table is required.

```text
paid Order
    |
    v
POST /payment/{order_id}/refund
    |
    +---- verify authenticated ownership
    +---- load Payment
    +---- require Order.status == paid
    +---- require Payment.status == paid
    +---- reject already-refunded payment
    +---- set Payment.status = refunded
    +---- set refunded_at
    +---- commit
    |
    v
PaymentResponse
```

Refund endpoint:

```text
POST /payment/{order_id}/refund
```

The existing `transaction_id` is preserved. A refund is rejected once fulfillment has started because the order is no longer in `paid` state.

The refund is currently a mock operation and does not contact an external payment provider.

## 8. Inventory Concurrency

Checkout uses SQLAlchemy `with_for_update()` to lock product rows before stock is checked and decremented.

Cancellation uses the same locking strategy before restoring stock.

This prevents concurrent transactions from incorrectly reserving the same inventory.

## 9. Shipping Lifecycle

```text
Checkout
   |
   v
Shipping created
   |
   v
processing
   |
   v
shipped
   |
   +--> shipped_at recorded
   |
   v
delivered
   |
   +--> delivered_at recorded
```

Shipping management is admin-only:

```text
PATCH /shipping/{order_id}
```

## 10. Persistence and Migrations

Alembic is the authoritative schema-management mechanism.

Relevant migration chain:

```text
40f98fd888bb_add_shipping_table.py
                |
                v
cff58edd10a9_add_payments_table.py
                |
                v
              HEAD
```

Step 30 created `payments` with:

```text
id
order_id
amount
status
transaction_id
created_at
paid_at
refunded_at
```

Step 31 requires no additional migration because refund state uses the existing `status` and `refunded_at` columns.

## 11. Redis Usage

Redis is shared by multiple application concerns:

```text
                 +---- Product catalog cache
                 |
Redis ------------+---- SlowAPI rate-limit storage
                 |
                 +---- Celery broker/result backend
```

## 12. Authentication and Authorization

JWT Bearer authentication protects user-specific operations.

```text
Request
  |
  v
JWT validation
  |
  v
get_current_user
  |
  +---- payment for own order
  |
  +---- refund for own order
  |
  +---- get_current_admin_user
             |
             v
         admin-only operation
```

Examples of admin-only operations:

- Product/category creation
- Order status management
- Shipping management

Payment and refund ownership are enforced at the Order query level.

## 13. Testing and CI

The application is tested with Pytest and HTTPX.

Latest verified local suite:

```text
33 passed
```

Coverage includes payment persistence, duplicate payment protection, payment ownership, successful refund, duplicate-refund rejection, refund ownership, refund rejection after processing, and missing-Payment handling.

CI workflow:

```text
GitHub Actions
      |
      +---- checkout
      +---- configure environment
      +---- Docker Compose build/start
      +---- PostgreSQL readiness
      +---- alembic upgrade head
      +---- pytest
```

## 14. Current Status

Latest implemented milestone:

```text
Step 31 — Payment Refund Flow
```

Latest local verification:

```text
33 passed
```

Alembic head:

```text
cff58edd10a9
```

## 15. Future Architecture Enhancements

- Real payment gateway adapter
- Payment-provider webhooks
- Idempotent payment/refund commands
- Refund audit/event history
- Structured logging
- Metrics and monitoring
- Distributed tracing
- API versioning
- Production security hardening
- Advanced inventory reservation/release policies
