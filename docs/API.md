# API Reference

Base URL (local development):

```text
http://localhost:8000
```

Interactive documentation is available from FastAPI at `/docs`.

## Authentication

User authentication uses JWT bearer tokens.

```text
POST /users/login
        ↓
access_token
        ↓
Authorization: Bearer <token>
```

Swagger's `Authorize` flow uses `POST /users/login` as the OAuth2 token endpoint.

## User API

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| POST | `/users/` | Public | Register a user |
| POST | `/users/login` | Public | Authenticate and obtain JWT |
| GET | `/users/me` | Bearer JWT | Get current user |
| GET | `/users/admin-only` | Admin JWT | Verify superuser access |

### UserCreate

```json
{
  "email": "user@example.com",
  "password": "minimum 8 characters"
}
```

### UserResponse

```text
id
email
is_active
is_superuser
```

## Category API

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| GET | `/categories/` | Public | List categories |
| POST | `/categories/` | Admin JWT | Create a category |

### CategoryCreate

```json
{
  "name": "Electronics",
  "description": "Electronic products"
}
```

## Product API

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| GET | `/products/` | Public | List products |
| GET | `/products/{product_id}` | Public | Get one product by ID |
| POST | `/products/` | Admin JWT | Create a product |

### ProductCreate

```json
{
  "title": "Test Laptop",
  "description": "A test product",
  "price": 1200,
  "stock_quantity": 10,
  "is_active": true,
  "category_id": 1
}
```

`category_id` must reference an existing category.

### ProductResponse

```text
id
title
description
price
stock_quantity
is_active
category_id
category
```

### Get Product By ID

```text
GET /products/{product_id}
```

Returns the product matching `product_id`.

Response when the product exists:

```json
{
  "id": 1,
  "title": "Laptop",
  "description": "Development laptop",
  "price": 1200,
  "stock_quantity": 10,
  "is_active": true,
  "category_id": 1
}
```

Response when the product does not exist:

```text
404 Not Found
```

## Cart API

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| GET | `/cart/` | Bearer JWT | Get current user's cart |
| POST | `/cart/` | Bearer JWT | Add/update a cart item |
| DELETE | `/cart/{item_id}` | Bearer JWT | Remove a cart item |

### CartItemCreate

```json
{
  "product_id": 1,
  "quantity": 1
}
```

## Order API

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| POST | `/orders/checkout` | Bearer JWT | Checkout current cart |
| GET | `/orders/` | Bearer JWT | List current user's orders |
| PATCH | `/orders/{order_id}/status` | Admin JWT | Update order status |
| POST | `/orders/{order_id}/cancel` | Bearer JWT | Cancel an order |

### CheckoutRequest

```json
{
  "address": "Example address",
  "city": "Baku",
  "postal_code": "AZ1000"
}
```

Checkout performs stock reservation and creates the order, order items, and shipping information transactionally.

## Payment API

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| POST | `/payment/process` | Bearer JWT | Process a payment |
| GET | `/payment/orders/{order_id}` | Bearer JWT | Get payment details for an order |
| POST | `/payment/{order_id}/refund` | Bearer JWT | Refund a paid order |
| POST | `/payment/webhook` | HMAC signature | Process provider webhook |

### PaymentRequest

```json
{
  "order_id": 1,
  "card_number": "6037991122334455",
  "idempotency_key": "optional-key"
}
```

`idempotency_key` is optional and prevents duplicate payment processing when the same key is replayed for the same order.

### PaymentWebhookRequest

```json
{
  "transaction_id": "transaction-id",
  "status": "paid",
  "event_id": "provider-event-id"
}
```
### PaymentDetailsResponse

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

### Get Order Payment

GET /payment/orders/{order_id}

Returns payment details for an order belonging to the authenticated user.

If the order does not exist or does not belong to the current user:

404 Not Found

If the order has no payment:

404 Not Found

Webhook authentication uses the configured `PAYMENT_WEBHOOK_SECRET` and HMAC-SHA256 signature validation.

## Shipping API

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| PATCH | `/shipping/{order_id}` | Admin JWT | Update carrier and tracking information |

### ShippingUpdate

```json
{
  "carrier": "Example Carrier",
  "tracking_number": "TRACK123"
}
```

## Observability API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/metrics` | Prometheus metrics |
| GET | `/` | API root/health-style endpoint |

Current Prometheus metrics include:

```text
http_requests_total
http_request_duration_seconds
```

## Current Verified API Surface

```text  id="5lmm0r"
POST   /users/
POST   /users/login
GET    /users/me
GET    /users/admin-only
GET    /categories/
POST   /categories/
GET    /products/
GET    /products/{product_id}
POST   /products/
GET    /cart/
POST   /cart/
DELETE /cart/{item_id}
POST   /orders/checkout
GET    /orders/
PATCH  /orders/{order_id}/status
POST   /orders/{order_id}/cancel
POST   /payment/webhook
POST   /payment/process
GET    /payment/orders/{order_id}
POST   /payment/{order_id}/refund
PATCH  /shipping/{order_id}
GET    /metrics
GET    /
```
## Frontend CI Validation

GitHub Actions validates the frontend with:

```text
npm ci
npm run lint
npm run build
```

The endpoint list and schemas above were verified against the running application's generated OpenAPI specification during the current development milestone.
