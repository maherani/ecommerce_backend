const API_BASE_URL = "http://localhost:8000";

async function authenticatedFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const headers = new Headers(init.headers);

  headers.set("Authorization", `Bearer ${token}`);

  return fetch(input, {
    ...init,
    headers,
  });
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();

  body.append("username", email);
  body.append("password", password);

  const response = await fetch(`${API_BASE_URL}/users/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });

  if (!response.ok) {
    throw new Error("Invalid email or password");
  }

  return response.json();
}

export async function getProducts() {
  const response = await fetch(`${API_BASE_URL}/products/`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function getCategories() {
  const response = await fetch(`${API_BASE_URL}/categories/`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function getCurrentUser() {
  const response = await authenticatedFetch(`${API_BASE_URL}/users/me`);

  if (!response.ok) {
    throw new Error(`Authentication failed: ${response.status}`);
  }

  return response.json();
}

export async function getProduct(productId: number) {
  const response = await fetch(`${API_BASE_URL}/products/${productId}`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function getCart() {
  const response = await authenticatedFetch(`${API_BASE_URL}/cart/`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function addToCart(productId: number, quantity: number) {
  const response = await authenticatedFetch(`${API_BASE_URL}/cart/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      product_id: productId,
      quantity,
    }),
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function removeFromCart(itemId: number) {
  const response = await authenticatedFetch(
    `${API_BASE_URL}/cart/${itemId}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
}
export async function checkout(
  address: string,
  city: string,
  postalCode: string,
) {
  const response = await authenticatedFetch(`${API_BASE_URL}/orders/checkout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      address,
      city,
      postal_code: postalCode,
    }),
  });

  if (!response.ok) {
    throw new Error(`Checkout failed: ${response.status}`);
  }

  return response.json();
}
export async function getOrders() {
  const response = await authenticatedFetch(`${API_BASE_URL}/orders/`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function getAdminOrders() {
  const response = await authenticatedFetch(`${API_BASE_URL}/orders/admin`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export async function cancelOrder(orderId: number) {
  const response = await authenticatedFetch(
    `${API_BASE_URL}/orders/${orderId}/cancel`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    throw new Error(`Cancel order failed: ${response.status}`);
  }

  return response.json();
}

export async function updateOrderStatus(
  orderId: number,
  newStatus: string,
) {
  const response = await authenticatedFetch(
    `${API_BASE_URL}/orders/${orderId}/status?new_status=${encodeURIComponent(newStatus)}`,
    {
      method: "PATCH",
    },
  );

  if (!response.ok) {
    throw new Error(`Update order status failed: ${response.status}`);
  }

  return response.json();
}

export async function processPayment(
  orderId: number,
  idempotencyKey?: string,
) {
  const response = await authenticatedFetch(`${API_BASE_URL}/payment/process`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      order_id: orderId,
      ...(idempotencyKey ? { idempotency_key: idempotencyKey } : {}),
    }),
  });

  if (!response.ok) {
    throw new Error(`Payment failed: ${response.status}`);
  }

  return response.json();
}

export async function refundPayment(orderId: number) {
  const response = await authenticatedFetch(
    `${API_BASE_URL}/payment/${orderId}/refund`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    throw new Error(`Refund failed: ${response.status}`);
  }

  return response.json();
}

export async function getOrderPayment(orderId: number) {
  const response = await authenticatedFetch(
    `${API_BASE_URL}/payment/orders/${orderId}`,
  );

  if (!response.ok) {
    throw new Error(`Get payment failed: ${response.status}`);
  }

  return response.json();
}