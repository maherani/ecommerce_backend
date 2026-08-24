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
