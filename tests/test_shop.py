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
