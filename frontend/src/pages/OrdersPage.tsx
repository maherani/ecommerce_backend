import { useEffect, useState } from "react";

import type { Order } from "../types/order";
import type { Payment } from "../types/payment";

import {
  cancelOrder,
  getOrderPayment,
  getOrders,
  processPayment,
  refundPayment,
} from "../services/api";


function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [payments, setPayments] = useState<Record<number, Payment>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [cancellingOrderId, setCancellingOrderId] = useState<number | null>(
    null,
  );

  const [payingOrderId, setPayingOrderId] = useState<number | null>(null);

  const [refundingOrderId, setRefundingOrderId] = useState<number | null>(
  null,
  );


  async function handleCancelOrder(orderId: number) {
    setCancellingOrderId(orderId);
    setError(null);

    try {
      const updatedOrder = await cancelOrder(orderId);

      setOrders((currentOrders) =>
        currentOrders.map((order) =>
          order.id === orderId ? updatedOrder : order,
        ),
      );
    } catch (err) {
      console.error(err);
      setError("Failed to cancel order.");
    } finally {
      setCancellingOrderId(null);
    }
  }

async function handlePayment(orderId: number) {
  setPayingOrderId(orderId);
  setError(null);

  try {
    const idempotencyKey = crypto.randomUUID();

    await processPayment(orderId, idempotencyKey);

    const payment = await getOrderPayment(orderId);

    setPayments((currentPayments) => ({
      ...currentPayments,
      [orderId]: payment,
    }));
    setOrders((currentOrders) =>
      currentOrders.map((order) =>
        order.id === orderId
          ? { ...order, status: "paid" }
          : order,
      ),
    );
  } catch (err) {
    console.error(err);
    setError("Payment failed.");
  } finally {
    setPayingOrderId(null);
  }
}

async function handleRefund(orderId: number) {
  setRefundingOrderId(orderId);
  setError(null);

  try {
    await refundPayment(orderId);

    const payment = await getOrderPayment(orderId);

    setPayments((currentPayments) => ({
      ...currentPayments,
      [orderId]: payment,
    }));

    setOrders((currentOrders) =>
      currentOrders.map((order) =>
        order.id === orderId
          ? { ...order, status: "refunded" }
          : order,
      ),
    );
  } catch (err) {
    console.error(err);
    setError("Refund failed.");
  } finally {
    setRefundingOrderId(null);
  }
}

useEffect(() => {
  void getOrders()
    .then(async (data: Order[]) => {
      setOrders(data);

      const payableOrders = data.filter(
        (order) =>
          order.status === "paid" || order.status === "refunded",
      );

      const paymentResults = await Promise.all(
        payableOrders.map(async (order) => {
          try {
            const payment = await getOrderPayment(order.id);
            return [order.id, payment] as const;
          } catch (err) {
            console.error(
              `Failed to load payment for order ${order.id}:`,
              err,
            );
            return null;
          }
        }),
      );

      const paymentMap: Record<number, Payment> = {};

      for (const result of paymentResults) {
        if (result) {
          paymentMap[result[0]] = result[1];
        }
      }

      setPayments(paymentMap);
    })
    .catch((err) => {
      console.error(err);
      setError("Failed to load orders.");
    })
    .finally(() => {
      setLoading(false);
    });
}, []);

  if (loading) {
    return <p>Loading orders...</p>;
  }

  if (error && orders.length === 0) {
    return <p>{error}</p>;
  }

  return (
    <section>
      <h2>Orders</h2>

      {error && <p>{error}</p>}

      {orders.length === 0 ? (
        <p>You have no orders.</p>
      ) : (
        <div>
          {orders.map((order) => (
            <article key={order.id}>
              <h3>Order #{order.id}</h3>

              <p>Status: {order.status}</p>
              {(() => {
                const payment = payments[order.id];

                if (!payment) {
                  return null;
                }

                return (
                  <div>
                    <h4>Payment</h4>

                    <p>Payment status: {payment.status}</p>

                    <p>Amount: ${payment.amount.toFixed(2)}</p>

                    <p>
                      Transaction ID: {payment.transaction_id ?? "N/A"}
                    </p>

                    <p>
                      Created:{" "}
                      {new Date(payment.created_at).toLocaleString()}
                    </p>

                    {payment.paid_at && (
                      <p>
                        Paid: {new Date(payment.paid_at).toLocaleString()}
                      </p>
                    )}

                    {payment.refunded_at && (
                      <p>
                        Refunded: {new Date(payment.refunded_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                );
              })()}
              {order.status === "pending" && (
                <button
                  type="button"
                  onClick={() => handleCancelOrder(order.id)}
                  disabled={cancellingOrderId === order.id}
                >
                  {cancellingOrderId === order.id
                    ? "Cancelling..."
                    : "Cancel Order"}
                </button>
              )}

              {order.status === "pending" && (
                <button
                  type="button"
                  onClick={() => handlePayment(order.id)}
                  disabled={payingOrderId === order.id}
                >
                  {payingOrderId === order.id ? "Processing..." : "Pay Order"}
                </button>
              )}

              {order.status === "paid" && (
                <button
                  type="button"
                  onClick={() => handleRefund(order.id)}
                  disabled={refundingOrderId === order.id}
                >
                  {refundingOrderId === order.id
                    ? "Refunding..."
                    : "Refund Order"}
                </button>
              )}

              <p>
                Created:{" "}
                {new Date(order.created_at).toLocaleString()}
              </p>

              {order.items.map((item) => (
                <div key={item.id}>
                  <p>
                    {item.product?.title ?? `Product #${item.product_id}`}
                  </p>
                  <p>Quantity: {item.quantity}</p>
                  <p>Unit price: ${item.unit_price.toFixed(2)}</p>
                </div>
              ))}

              {order.shipping && (
                <div>
                  <h4>Shipping</h4>
                  <p>{order.shipping.address}</p>
                  <p>{order.shipping.city}</p>
                  <p>{order.shipping.postal_code}</p>
                </div>
              )}

              <p>
                <strong>
                  Total: ${order.total_price.toFixed(2)}
                </strong>
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default OrdersPage;
