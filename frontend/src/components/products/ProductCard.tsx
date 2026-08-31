import type { Product } from "../../types/product";

interface ProductCardProps {
  product: Product;
}

function ProductCard({ product }: ProductCardProps) {
  return (
    <article className="product-card">
      <div className="product-card__image">
        <span>No Image</span>
      </div>

      <div className="product-card__content">
        <h3>{product.title}</h3>

        {product.description && (
          <p className="product-card__description">
            {product.description}
          </p>
        )}

        <p className="product-card__price">
          ${product.price.toFixed(2)}
        </p>

        <p className="product-card__stock">
          {product.stock_quantity > 0
            ? `${product.stock_quantity} in stock`
            : "Out of stock"}
        </p>

        <button type="button">
          View Product
        </button>
      </div>
    </article>
  );
}

export default ProductCard;