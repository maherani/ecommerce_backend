export interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  product?: {
    id: number;
    title: string;
    price: number;
    stock_quantity: number;
    is_active: boolean;
    category_id: number;
  };
}

export interface Shipping {
  id: number;
  order_id: number;
  address: string;
  city: string;
  postal_code: string;
  shipped_at?: string | null;
  delivered_at?: string | null;
}

export interface Order {
  id: number;
  user_id: number;
  total_price: number;
  status: string;
  created_at: string;
  items: OrderItem[];
  shipping?: Shipping | null;
}
