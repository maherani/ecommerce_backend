export interface Payment {
  id: number;
  order_id: number;
  amount: number;
  status: string;
  transaction_id: string | null;
  created_at: string;
  paid_at: string | null;
  refunded_at: string | null;
}
