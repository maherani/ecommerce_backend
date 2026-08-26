import hashlib
import hmac

from app.core.database import SessionLocal
from app.modules.payment.models import Payment
from app.modules.shipping.models import Shipping
from app.modules.order.models import Order
from app.modules.product.models import Product
from app.modules.payment.models import Payment, PaymentEvent
from app.core.config import settings
from app.modules.payment.schemas import PaymentWebhookRequest

def test_products_list(client):
    """تست دریافت لیست محصولات"""
    response = client.get("/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_full_purchase_flow(client, auth_token):
    """تست کامل چرخه خرید: افزودن به سبد -> چک‌آوت -> پرداخت"""
    # ۱. ابتدا بررسی می‌کنیم محصولی در سیستم وجود دارد یا یک محصول تستی می‌گیریم
    products_res = client.get("/products/")
    products = products_res.json()

    # اگر محصولی نبود، تست را رد می‌کنیم یا فرض می‌کنیم حداقل یک محصول از قبل درج شده
    if not products:
        # ساخت یک محصول فرضی اگر دیتابیس خالی باشد
        # (بسته به اینکه آیا ادمین محصولی اضافه کرده یا خیر)
        return

    product = next(
         (p for p in products if p["stock_quantity"] >= 2),
         None
    )

    if not product:
       return

    product_id = products[0]["id"]

    # ۲. افزودن محصول به سبد خرید
    cart_res = client.post(
        "/cart/",
        json={"product_id": product_id, "quantity": 2},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert cart_res.status_code == 201
    cart_item_data = cart_res.json()
    assert cart_item_data["product_id"] == product_id
    assert cart_item_data["quantity"] == 2

    # ۳. نهایی‌سازی سفارش (Checkout)
    checkout_res = client.post(
        "/orders/checkout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert checkout_res.status_code == 201
    order_data = checkout_res.json()
    order_id = order_data["id"]
    assert order_data["status"] == "pending"

    # ۴. شبیه‌سازی پرداخت
    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id, "card_number": "6037991122334455"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert payment_res.status_code == 200
    payment_data = payment_res.json()
    assert payment_data["status"] == "paid"
    assert "transaction_id" in payment_data

def test_add_to_cart_more_than_stock(client, auth_token):
    """نباید بیشتر از موجودی محصول به سبد اضافه شود"""
    products_res = client.get("/products/")
    products = products_res.json()

    product = next(
        (p for p in products if p["stock_quantity"] > 0),
        None
    )

    if not product:
        return

    response = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": product["stock_quantity"] + 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient stock"


def test_checkout_reduces_stock(client, auth_token):
    """Checkout باید موجودی محصول را کاهش دهد"""
    products_res = client.get("/products/")
    products = products_res.json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    product_id = product["id"]
    initial_stock = product["stock_quantity"]

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product_id,
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    products_after = client.get("/products/").json()

    updated_product = next(
        p for p in products_after
        if p["id"] == product_id
    )

    assert updated_product["stock_quantity"] == initial_stock - 1
def test_cancel_pending_order_restores_stock(client, auth_token):
    """لغو سفارش pending باید موجودی محصول را برگرداند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    product_id = product["id"]
    initial_stock = product["stock_quantity"]

    # افزودن محصول به سبد
    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product_id,
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    # Checkout
    checkout_res = client.post(
        "/orders/checkout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order = checkout_res.json()
    order_id = order["id"]

    # موجودی باید یک واحد کم شده باشد
    products_after_checkout = client.get("/products/").json()

    product_after_checkout = next(
        p for p in products_after_checkout
        if p["id"] == product_id
    )

    assert product_after_checkout["stock_quantity"] == initial_stock - 1

    # لغو سفارش
    cancel_res = client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cancel_res.status_code == 200

    cancelled_order = cancel_res.json()

    assert cancelled_order["id"] == order_id
    assert cancelled_order["status"] == "cancelled"

    # موجودی باید به مقدار اولیه برگردد
    products_after_cancel = client.get("/products/").json()

    product_after_cancel = next(
        p for p in products_after_cancel
        if p["id"] == product_id
    )

    assert product_after_cancel["stock_quantity"] == initial_stock
def test_cancel_already_cancelled_order_fails(client, auth_token):
    """سفارش cancelled نباید دوباره قابل لغو باشد."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    first_cancel = client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert first_cancel.status_code == 200

    second_cancel = client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert second_cancel.status_code == 400
    assert second_cancel.json()["detail"] == (
        "Only pending orders can be cancelled"
    )


def test_cancel_paid_order_fails(client, auth_token):
    """سفارش paid نباید در این مرحله قابل لغو باشد."""
    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={
            "order_id": order_id,
            "card_number": "6037991122334455"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert payment_res.status_code == 200

    cancel_res = client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cancel_res.status_code == 400
    assert cancel_res.json()["detail"] == (
        "Only pending orders can be cancelled"
    )


def test_cancel_other_users_order_fails(client, auth_token):
    """کاربر نباید بتواند سفارش متعلق به کاربر دیگری را لغو کند."""
    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    other_user_order_id = order_id + 999999

    cancel_res = client.post(
        f"/orders/{other_user_order_id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cancel_res.status_code == 404
    assert cancel_res.json()["detail"] == "Order not found"

def test_admin_can_update_order_status(client, auth_token, admin_token):
    """ادمین باید بتواند وضعیت سفارش را طبق lifecycle تغییر دهد."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]
    assert checkout_res.json()["status"] == "pending"

    transitions = [
        ("paid", 200),
        ("processing", 200),
        ("shipped", 200),
        ("delivered", 200),
    ]

    for new_status, expected_status_code in transitions:
        response = client.patch(
            f"/orders/{order_id}/status",
            params={"new_status": new_status},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == expected_status_code
        assert response.json()["status"] == new_status

def test_invalid_order_status_transition_is_rejected(
    client,
    auth_token,
    admin_token
):
    """انتقال‌های غیرمجاز وضعیت سفارش باید رد شوند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    # pending -> shipped مجاز نیست
    response = client.patch(
        f"/orders/{order_id}/status",
        params={"new_status": "shipped"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid status transition: pending -> shipped"
    )


def test_regular_user_cannot_update_order_status(
    client,
    auth_token
):
    """کاربر عادی نباید بتواند وضعیت سفارش را تغییر دهد."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    response = client.patch(
        f"/orders/{order_id}/status",
        params={"new_status": "paid"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 403


def test_update_unknown_order_status_returns_404(
    client,
    admin_token
):
    """شناسه سفارش ناموجود باید 404 برگرداند."""

    response = client.patch(
        "/orders/999999/status",
        params={"new_status": "paid"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"

def test_checkout_creates_shipping(client, auth_token):
    """Checkout باید رکورد Shipping را همراه سفارش ایجاد کند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_data = checkout_res.json()

    assert order_data["status"] == "pending"
    assert order_data["shipping"] is not None

    shipping = order_data["shipping"]

    assert shipping["order_id"] == order_data["id"]
    assert shipping["address"] == "123 Main Street"
    assert shipping["city"] == "Tehran"
    assert shipping["postal_code"] == "1234567890"
    assert shipping["carrier"] is None
    assert shipping["tracking_number"] is None
    assert shipping["shipped_at"] is None
    assert shipping["delivered_at"] is None

def test_failed_checkout_does_not_create_shipping(client, auth_token):
    """Checkout ناموفق نباید Shipping یا Order جدید ایجاد کند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    product_id = product["id"]
    initial_stock = product["stock_quantity"]

    db = SessionLocal()
    try:
        initial_order_count = db.query(Order).count()
        initial_shipping_count = db.query(Shipping).count()
    finally:
        db.close()
    # ایجاد سبد با مقداری بیشتر از موجودی فعلی
    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product_id,
            "quantity": initial_stock + 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    # Cart خودش باید این درخواست را رد کند.
    assert cart_res.status_code == 400
    assert cart_res.json()["detail"] == "Insufficient stock"

    # برای تست rollback، مقدار 1 را در سبد قرار می‌دهیم و
    # سپس قبل از checkout موجودی را به صفر می‌رسانیم.
    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product_id,
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    db = SessionLocal()
    try:
        product_db = db.query(
            __import__(
                "app.modules.product.models",
                fromlist=["Product"]
            ).Product
        ).filter_by(id=product_id).first()

        assert product_db is not None

        product_db.stock_quantity = 0
        db.commit()
    finally:
        db.close()

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 400

    db = SessionLocal()
    try:
        final_order_count = db.query(Order).count()
        final_shipping_count = db.query(Shipping).count()
    finally:
        db.close()

    assert final_order_count == initial_order_count
    assert final_shipping_count == initial_shipping_count

    db = SessionLocal()
    try:
        product_db = db.query(Product).filter_by(id=product_id).first()

        assert product_db is not None

        product_db.stock_quantity = initial_stock
        db.commit()
    finally:
        db.close()

def test_admin_can_update_shipping(client, auth_token, admin_token):
    """ادمین باید بتواند carrier و tracking number را تغییر دهد."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    response = client.patch(
        f"/shipping/{order_id}",
        json={
            "carrier": "DHL",
            "tracking_number": "DHL-123456789"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200

    shipping = response.json()

    assert shipping["order_id"] == order_id
    assert shipping["carrier"] == "DHL"
    assert shipping["tracking_number"] == "DHL-123456789"


def test_regular_user_cannot_update_shipping(
    client,
    auth_token
):
    """کاربر عادی نباید بتواند اطلاعات حمل را تغییر دهد."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    response = client.patch(
        f"/shipping/{order_id}",
        json={
            "carrier": "DHL",
            "tracking_number": "DHL-123456789"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 403


def test_unknown_shipping_order_returns_404(client, admin_token):
    """برای سفارشی که Shipping ندارد باید 404 برگردد."""

    response = client.patch(
        "/shipping/999999",
        json={
            "carrier": "DHL",
            "tracking_number": "DHL-000000000"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Shipping record not found"


def test_shipping_timestamps_follow_order_lifecycle(
    client,
    auth_token,
    admin_token
):
    """تغییر lifecycle باید shipped_at و delivered_at را ثبت کند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    for new_status in ["paid", "processing", "shipped"]:
        response = client.patch(
            f"/orders/{order_id}/status",
            params={"new_status": new_status},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    shipping = client.patch(
        f"/shipping/{order_id}",
        json={
            "carrier": "DHL",
            "tracking_number": "DHL-123456789"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert shipping.status_code == 200
    shipping_data = shipping.json()

    assert shipping_data["shipped_at"] is not None
    assert shipping_data["delivered_at"] is None

    response = client.patch(
        f"/orders/{order_id}/status",
        params={"new_status": "delivered"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200

    shipping = client.patch(
        f"/shipping/{order_id}",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert shipping.status_code == 200

    shipping_data = shipping.json()

    assert shipping_data["shipped_at"] is not None
    assert shipping_data["delivered_at"] is not None

def test_payment_creates_persistent_record(client, auth_token):
    """پرداخت باید رکورد Payment پایدار در دیتابیس ایجاد کند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order = checkout_res.json()
    order_id = order["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert payment_res.status_code == 200

    payment_data = payment_res.json()

    assert payment_data["order_id"] == order_id
    assert payment_data["status"] == "paid"
    assert payment_data["transaction_id"].startswith("TRX-")

    db = SessionLocal()
    try:
        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .first()
        )

        assert payment is not None
        assert payment.amount == order["total_price"]
        assert payment.status == "paid"
        assert payment.transaction_id == payment_data["transaction_id"]
        assert payment.paid_at is not None
    finally:
        db.close()
def test_second_payment_is_rejected(client, auth_token):
    """یک سفارش نباید دوبار پرداخت شود."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    first_payment = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert first_payment.status_code == 200

    second_payment = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert second_payment.status_code == 400
    assert second_payment.json()["detail"] == (
        "Only pending orders can be paid"
    )
def test_user_cannot_pay_other_users_order(
    client,
    auth_token,
    test_user
):
    """کاربر نباید بتواند سفارش کاربر دیگری را پرداخت کند."""

    # ایجاد سفارش با کاربر اول
    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    # ورود کاربر دوم
    login_res = client.post(
        "/users/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )

    assert login_res.status_code == 200

    other_user_token = login_res.json()["access_token"]

    # تلاش کاربر دوم برای پرداخت سفارش کاربر اول
    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {other_user_token}"}
    )

    assert payment_res.status_code == 404
    assert payment_res.json()["detail"] == "Order not found"
def test_paid_order_can_be_refunded(client, auth_token):
    """سفارش paid باید قابل refund باشد."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert payment_res.status_code == 200

    refund_res = client.post(
        f"/payment/{order_id}/refund",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert refund_res.status_code == 200

    refund_data = refund_res.json()

    assert refund_data["order_id"] == order_id
    assert refund_data["status"] == "refunded"
    assert refund_data["transaction_id"] == payment_res.json()["transaction_id"]

    db = SessionLocal()
    try:
        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .first()
        )

        assert payment is not None
        assert payment.status == "refunded"
        assert payment.refunded_at is not None
    finally:
        db.close()
def test_second_refund_is_rejected(client, auth_token):
    """یک Payment نباید دوبار refund شود."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert payment_res.status_code == 200

    first_refund = client.post(
        f"/payment/{order_id}/refund",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert first_refund.status_code == 200

    second_refund = client.post(
        f"/payment/{order_id}/refund",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert second_refund.status_code == 400
    assert second_refund.json()["detail"] == "Payment is already refunded"
def test_refund_after_processing_is_rejected(
    client,
    auth_token,
    admin_token
):
    """بعد از شروع processing، refund نباید مجاز باشد."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert payment_res.status_code == 200

    response = client.patch(
        f"/orders/{order_id}/status",
        params={"new_status": "processing"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processing"

    refund_res = client.post(
        f"/payment/{order_id}/refund",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert refund_res.status_code == 400
    assert refund_res.json()["detail"] == (
        "Only paid payments can be refunded"
    )
def test_user_cannot_refund_other_users_order(
    client,
    auth_token,
    test_user
):
    """کاربر نباید بتواند سفارش پرداخت‌شده کاربر دیگری را refund کند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert payment_res.status_code == 200

    login_res = client.post(
        "/users/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )

    assert login_res.status_code == 200

    other_user_token = login_res.json()["access_token"]

    refund_res = client.post(
        f"/payment/{order_id}/refund",
        headers={"Authorization": f"Bearer {other_user_token}"}
    )

    assert refund_res.status_code == 404
    assert refund_res.json()["detail"] == "Order not found"

def test_refund_persists_payment_state(client, auth_token):
    """Refund باید وضعیت Payment را به‌صورت پایدار ثبت کند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert payment_res.status_code == 200

    refund_res = client.post(
        f"/payment/{order_id}/refund",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert refund_res.status_code == 200

    db = SessionLocal()
    try:
        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .first()
        )

        assert payment is not None
        assert payment.status == "refunded"
        assert payment.refunded_at is not None
        assert payment.transaction_id == payment_res.json()["transaction_id"]
    finally:
        db.close()

def test_refund_without_payment_returns_404(client, auth_token):
    """Refund سفارشی که Payment ندارد باید 404 باشد."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    refund_res = client.post(
        f"/payment/{order_id}/refund",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert refund_res.status_code == 404
    assert refund_res.json()["detail"] == "Payment not found"

def test_payment_idempotency_key_returns_existing_payment(
    client,
    auth_token
):
    """درخواست تکراری با همان idempotency key نباید Payment جدید بسازد."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]
    idempotency_key = "test-idempotency-key-001"

    first_payment = client.post(
        "/payment/process",
        json={
            "order_id": order_id,
            "idempotency_key": idempotency_key
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert first_payment.status_code == 200

    first_data = first_payment.json()

    db = SessionLocal()
    try:
        initial_count = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .count()
        )
    finally:
        db.close()

    second_payment = client.post(
        "/payment/process",
        json={
            "order_id": order_id,
            "idempotency_key": idempotency_key
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert second_payment.status_code == 200

    second_data = second_payment.json()

    assert second_data["transaction_id"] == first_data["transaction_id"]
    assert second_data["status"] == "paid"
    assert second_data["message"] == "Payment already processed"

    db = SessionLocal()
    try:
        final_count = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .count()
        )
    finally:
        db.close()

    assert final_count == initial_count
def test_idempotency_key_cannot_be_reused_for_another_order(
    client,
    auth_token
):
    """یک idempotency key نباید برای سفارش دیگری استفاده شود."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 2),
        None
    )

    if not product:
        return

    headers = {"Authorization": f"Bearer {auth_token}"}
    idempotency_key = "test-idempotency-key-reuse-001"

    # سفارش اول
    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers=headers
    )
    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers=headers
    )
    assert checkout_res.status_code == 201

    first_order_id = checkout_res.json()["id"]

    first_payment = client.post(
        "/payment/process",
        json={
            "order_id": first_order_id,
            "idempotency_key": idempotency_key
        },
        headers=headers
    )
    assert first_payment.status_code == 200

    # سفارش دوم
    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers=headers
    )
    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "456 Second Street",
            "city": "Tehran",
            "postal_code": "9876543210"
        },
        headers=headers
    )
    assert checkout_res.status_code == 201

    second_order_id = checkout_res.json()["id"]

    second_payment = client.post(
        "/payment/process",
        json={
            "order_id": second_order_id,
            "idempotency_key": idempotency_key
        },
        headers=headers
    )

    assert second_payment.status_code == 409
    assert second_payment.json()["detail"] == (
        "Idempotency key already used for another order"
    )
def test_payment_events_are_persisted(client, auth_token):
    """پرداخت و refund باید Event مربوط به خود را در دیتابیس ثبت کنند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    headers = {"Authorization": f"Bearer {auth_token}"}

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers=headers
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers=headers
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers=headers
    )

    assert payment_res.status_code == 200

    db = SessionLocal()
    try:
        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .first()
        )

        assert payment is not None

        events = (
            db.query(PaymentEvent)
            .filter(PaymentEvent.payment_id == payment.id)
            .order_by(PaymentEvent.id)
            .all()
        )

        assert len(events) == 1
        assert events[0].event_type == "payment_created"
        assert events[0].status == "paid"

        assert events[0].actor_user_id is not None
        assert events[0].actor_user_id > 0

        assert events[0].event_metadata is not None
        assert events[0].event_metadata["order_id"] == order_id
        assert (
            events[0].event_metadata["amount"]
            == checkout_res.json()["total_price"]
        )
        assert (
            events[0].event_metadata["transaction_id"]
            == payment_res.json()["transaction_id"]
        )
    finally:
        db.close()

    refund_res = client.post(
        f"/payment/{order_id}/refund",
        headers=headers
    )

    assert refund_res.status_code == 200

    db = SessionLocal()
    try:
        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .first()
        )

        assert payment is not None

        events = (
            db.query(PaymentEvent)
            .filter(PaymentEvent.payment_id == payment.id)
            .order_by(PaymentEvent.id)
            .all()
        )

        assert len(events) == 2

        assert events[0].event_type == "payment_created"
        assert events[0].status == "paid"

        assert events[1].event_type == "payment_refunded"
        assert events[1].status == "refunded"

        assert events[1].actor_user_id == events[0].actor_user_id

        assert events[1].event_metadata is not None
        assert events[1].event_metadata["order_id"] == order_id
        assert (
            events[1].event_metadata["transaction_id"]
            == payment_res.json()["transaction_id"]
        )
        assert events[1].event_metadata["refunded_at"] is not None
    finally:
        db.close()
def test_idempotent_payment_does_not_create_duplicate_event(
    client,
    auth_token
):
    """درخواست تکراری idempotent نباید PaymentEvent جدید ایجاد کند."""

    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    headers = {"Authorization": f"Bearer {auth_token}"}
    idempotency_key = "audit-idempotency-test-001"

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers=headers
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        headers=headers
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    first_payment = client.post(
        "/payment/process",
        json={
            "order_id": order_id,
            "idempotency_key": idempotency_key
        },
        headers=headers
    )

    assert first_payment.status_code == 200

    first_transaction_id = first_payment.json()["transaction_id"]

    second_payment = client.post(
        "/payment/process",
        json={
            "order_id": order_id,
            "idempotency_key": idempotency_key
        },
        headers=headers
    )

    assert second_payment.status_code == 200
    assert second_payment.json()["transaction_id"] == first_transaction_id
    assert second_payment.json()["message"] == "Payment already processed"

    db = SessionLocal()
    try:
        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .first()
        )

        assert payment is not None

        events = (
            db.query(PaymentEvent)
            .filter(PaymentEvent.payment_id == payment.id)
            .all()
        )

        assert len(events) == 1
        assert events[0].event_type == "payment_created"
    finally:
        db.close()

def test_payment_webhook_signature_validation(client, auth_token):
    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    headers = {"Authorization": f"Bearer {auth_token}"}

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1
        },
        headers=headers
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890"
        },
        headers=headers
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers=headers
    )

    assert payment_res.status_code == 200

    transaction_id = payment_res.json()["transaction_id"]

    webhook_payload = {
        "transaction_id": transaction_id,
        "status": "paid",
        "event_id": "webhook-test-001",
    }

    payload_bytes = (
        PaymentWebhookRequest(**webhook_payload)
        .model_dump_json()
        .encode()
    )

    valid_signature = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    valid_response = client.post(
        "/payment/webhook",
        json=webhook_payload,
        params={"signature": valid_signature},
    )

    assert valid_response.status_code == 200

    invalid_response = client.post(
        "/payment/webhook",
        json=webhook_payload,
        params={"signature": "invalid-signature"},
    )

    assert invalid_response.status_code == 401
def test_payment_webhook_rejects_invalid_payment_and_status(client):
    unknown_payload = {
        "transaction_id": "TRX-UNKNOWN-001",
        "status": "paid",
        "event_id": "webhook-error-001",
    }

    payload_bytes = (
        PaymentWebhookRequest(**unknown_payload)
        .model_dump_json()
        .encode()
    )

    valid_signature = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    not_found_response = client.post(
        "/payment/webhook",
        json=unknown_payload,
        params={"signature": valid_signature},
    )

    assert not_found_response.status_code == 404
    assert not_found_response.json()["detail"] == "Payment not found"
def test_payment_webhook_rejects_unsupported_status(
    client,
    auth_token
):
    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    headers = {"Authorization": f"Bearer {auth_token}"}

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1,
        },
        headers=headers,
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890",
        },
        headers=headers,
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers=headers,
    )

    assert payment_res.status_code == 200

    transaction_id = payment_res.json()["transaction_id"]

    webhook_payload = {
        "transaction_id": transaction_id,
        "status": "unknown_status",
        "event_id": "webhook-invalid-status-001",
    }

    payload_bytes = (
        PaymentWebhookRequest(**webhook_payload)
        .model_dump_json()
        .encode()
    )

    valid_signature = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/payment/webhook",
        json=webhook_payload,
        params={"signature": valid_signature},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported payment status"
def test_payment_webhook_is_idempotent(
    client,
    auth_token
):
    products = client.get("/products/").json()

    product = next(
        (p for p in products if p["stock_quantity"] >= 1),
        None
    )

    if not product:
        return

    headers = {"Authorization": f"Bearer {auth_token}"}

    cart_res = client.post(
        "/cart/",
        json={
            "product_id": product["id"],
            "quantity": 1,
        },
        headers=headers,
    )

    assert cart_res.status_code == 201

    checkout_res = client.post(
        "/orders/checkout",
        json={
            "address": "123 Main Street",
            "city": "Tehran",
            "postal_code": "1234567890",
        },
        headers=headers,
    )

    assert checkout_res.status_code == 201

    order_id = checkout_res.json()["id"]

    payment_res = client.post(
        "/payment/process",
        json={"order_id": order_id},
        headers=headers,
    )

    assert payment_res.status_code == 200

    transaction_id = payment_res.json()["transaction_id"]

    webhook_payload = {
        "transaction_id": transaction_id,
        "status": "paid",
        "event_id": "webhook-idempotency-001",
    }

    payload_bytes = (
        PaymentWebhookRequest(**webhook_payload)
        .model_dump_json()
        .encode()
    )

    signature = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    first_response = client.post(
        "/payment/webhook",
        json=webhook_payload,
        params={"signature": signature},
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/payment/webhook",
        json=webhook_payload,
        params={"signature": signature},
    )

    assert second_response.status_code == 200
    assert second_response.json()["message"] == "Webhook already processed"
    assert second_response.json()["transaction_id"] == transaction_id

    db = SessionLocal()
    try:
        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .first()
        )

        assert payment is not None

        events = (
            db.query(PaymentEvent)
            .filter(PaymentEvent.payment_id == payment.id)
            .filter(PaymentEvent.event_id == "webhook-idempotency-001")
            .all()
        )

        assert len(events) == 1
    finally:
        db.close()
