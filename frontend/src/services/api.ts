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