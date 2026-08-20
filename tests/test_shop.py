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
