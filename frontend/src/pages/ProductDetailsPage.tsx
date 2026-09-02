import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { addToCart, getProduct } from "../services/api";
import type { Product } from "../types/product";

function ProductDetailsPage() {
  const { productId } = useParams<{ productId: string }>();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addingToCart, setAddingToCart] = useState(false);
  const [cartMessage, setCartMessage] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    async function loadProduct() {
      if (!productId) {
        setError("Product ID is missing.");
        setLoading(false);
        return;
      }

      try {
        const data = await getProduct(Number(productId));
        setProduct(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load product.");
      } finally {
        setLoading(false);
      }
    }

    loadProduct();
  }, [productId]);

  if (loading) {
    return <p>Loading product...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  if (!product) {
    return <p>Product not found.</p>;
  }

  return (
    <section>
      <h2>{product.title}</h2>

      {product.description && <p>{product.description}</p>}

      <p>${product.price.toFixed(2)}</p>

      <p>
        {product.stock_quantity > 0
          ? `${product.stock_quantity} in stock`
          : "Out of stock"}
      </p>
      <div>
        <label htmlFor="quantity">Quantity</label>

        <input
          id="quantity"
          type="number"
          min="1"
          max={product.stock_quantity}
          value={quantity}
          onChange={(event) => {
            const value = Number(event.target.value);

            if (value >= 1 && value <= product.stock_quantity) {
              setQuantity(value);
            }
          }}
        />
      </div>

      <button
        type="button"
        disabled={addingToCart || product.stock_quantity === 0}
        onClick={async () => {
          try {
            setAddingToCart(true);
            setCartMessage(null);

            await addToCart(product.id, quantity);

            setCartMessage("Product added to cart.");
          } catch (err) {
            console.error(err);
            setCartMessage("Failed to add product to cart.");
          } finally {
            setAddingToCart(false);
          }
        }}
      >
        {addingToCart ? "Adding..." : "Add to Cart"}
      </button>

{cartMessage && <p>{cartMessage}</p>}
    </section>
  );
}

export default ProductDetailsPage;