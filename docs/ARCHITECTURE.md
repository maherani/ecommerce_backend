# Architecture

## 1. System Overview

The application is a Dockerized FastAPI e-commerce backend with PostgreSQL as the primary relational database and Redis as the shared infrastructure for caching, rate limiting, and Celery.

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

### Order relationships

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

Shipping stores:

```text
address
city
postal_code
carrier
tracking_number
shipped_at
delivered_at
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

Database constraints enforce:

- `payments.order_id` foreign key to `orders.id`
- unique `payments.order_id`
- unique `payments.transaction_id`

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

Step 30 adds persistent payment storage.

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
     +---- set Order.status = paid
     +---- commit
     |
     v
PaymentResponse
```

The current gateway is intentionally a mock implementation.

Real provider integration, webhook handling, idempotency keys, and refund processing are future enhancements.

## 7. Inventory Concurrency

Checkout uses SQLAlchemy `with_for_update()` to lock product rows before stock is checked and decremented.

Cancellation uses the same locking strategy before restoring stock.

This prevents concurrent transactions from incorrectly reserving the same inventory.

## 8. Shipping Lifecycle

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

## 9. Persistence and Migrations

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

Step 30 payment migration creates:

```text
payments
```

with:

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

## 10. Redis Usage

Redis is shared by multiple application concerns:

```text
                 +---- Product catalog cache
                 |
Redis ------------+---- SlowAPI rate-limit storage
                 |
                 +---- Celery broker/result backend
```

## 11. Authentication and Authorization

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
  +---- normal user access
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

## 12. Testing and CI

The application is tested with Pytest and HTTPX.

Latest verified suite:

```text
30 passed
```

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

## 13. Current Status

Latest documented milestone:

```text
Step 30 — Persistent Payment Records
```

Latest local verification reported:

```text
30 passed
```

Alembic head:

```text
cff58edd10a9
```

## 14. Future Architecture Enhancements

- Real payment gateway adapter
- Payment-provider webhooks
- Idempotent payment commands
- Refund service and refund state machine
- Payment audit/event history
- Structured logging
- Metrics and monitoring
- Distributed tracing
- API versioning
- Production security hardening
- Advanced inventory reservation/release policies
