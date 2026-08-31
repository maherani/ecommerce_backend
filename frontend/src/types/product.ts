export interface Product {
  id: number;
  title: string;
  description: string | null;
  price: number;
  stock_quantity: number;
  is_active: boolean;
  category_id: number;
}
