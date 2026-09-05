import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getCart, removeFromCart } from "../services/api";
import type { CartItem } from "../types/cart";

function CartPage() {
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCart() {
      try {
        const data = await getCart();
        setCartItems(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load cart.");
      } finally {
        setLoading(false);
      }
    }

    loadCart();
  }, []);

  if (loading) {
    return <p>Loading cart...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  const total = cartItems.reduce((sum, item) => {
    return sum + (item.product?.price ?? 0) * item.quantity;
  }, 0);

  return (
    <section>
      <h2>Shopping Cart</h2>

      {cartItems.length === 0 ? (
        <p>Your cart is empty.</p>
      ) : (
        <>
          <div>
            {cartItems.map((item) => (
              <article key={item.id}>
                <h3>{item.product?.title ?? "Product"}</h3>

                <p>Quantity: {item.quantity}</p>

                {item.product && (
                  <p>${item.product.price.toFixed(2)}</p>
                )}

                <button
                  type="button"
                  onClick={async () => {
                    try {
                      await removeFromCart(item.id);

                      setCartItems((currentItems) =>
                        currentItems.filter(
                          (currentItem) => currentItem.id !== item.id,
                        ),
                      );
                    } catch (err) {
                      console.error(err);
                      setError("Failed to remove item from cart.");
                    }
                  }}
                >
                  Remove
                </button>
              </article>
            ))}
          </div>

          <p>Total: ${total.toFixed(2)}</p>

          <div>
            <Link to="/checkout">Proceed to Checkout</Link>
          </div>
        </>
      )}
    </section>
  );
}

export default CartPage;
