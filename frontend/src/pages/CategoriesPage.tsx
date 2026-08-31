import { useEffect, useState } from "react";

import { getCategories } from "../services/api";
import type { Category } from "../types/category";

function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCategories() {
      try {
        const data = await getCategories();
        setCategories(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load categories.");
      } finally {
        setLoading(false);
      }
    }

    loadCategories();
  }, []);

  if (loading) {
    return <p>Loading categories...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <section>
      <h2>Categories</h2>

      {categories.length === 0 ? (
        <p>No categories available.</p>
      ) : (
        <ul>
          {categories.map((category) => (
            <li key={category.id}>
              <strong>{category.name}</strong>

              {category.description && (
                <p>{category.description}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default CategoriesPage;