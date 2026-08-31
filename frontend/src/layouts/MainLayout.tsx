import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface MainLayoutProps {
  children: ReactNode;
}

function MainLayout({ children }: MainLayoutProps) {
  return (
    <div>
      <header>
        <h1>E-Commerce Store</h1>

        <nav>
          <Link to="/">Home</Link>
          <Link to="/products">Products</Link>
          <Link to="/categories">Categories</Link>
          <Link to="/cart">Cart</Link>
        </nav>
      </header>

      <main>{children}</main>

      <footer>
        <p>E-Commerce Store</p>
      </footer>
    </div>
  );
}

export default MainLayout;
