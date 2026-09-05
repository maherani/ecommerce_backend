import { useEffect, useState } from "react";

import {
getAdminOrders,
updateOrderStatus,
} from "../services/api";
import type { Order } from "../types/order";

const nextStatus: Record<string, string | null> = {
pending: "paid",
paid: "processing",
processing: "shipped",
shipped: "delivered",
delivered: null,
cancelled: null,
};

function AdminOrdersPage() {
const [orders, setOrders] = useState<Order[]>([]);
const [loading, setLoading] = useState(true);
const [updatingOrderId, setUpdatingOrderId] = useState<number | null>(
null,
);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
async function loadOrders() {
try {
const data = await getAdminOrders();
setOrders(data);
} catch (err) {
console.error(err);
setError("Failed to load admin orders.");
} finally {
setLoading(false);
}
}
void loadOrders();

}, []);

async function handleStatusUpdate(
orderId: number,
status: string,
) {
setUpdatingOrderId(orderId);
setError(null);
try {
  const updatedOrder = await updateOrderStatus(orderId, status);

  setOrders((currentOrders) =>
    currentOrders.map((order) =>
      order.id === orderId ? updatedOrder : order,
    ),
  );
} catch (err) {
  console.error(err);
  setError("Failed to update order status.");
} finally {
  setUpdatingOrderId(null);
}

}

if (loading) {
return <p>Loading admin orders...</p>;
}

if (error && orders.length === 0) {
return <p>{error}</p>;
}

return ( <section> <h2>Admin Orders</h2>
  {error && <p>{error}</p>}

  {orders.length === 0 ? (
    <p>No orders found.</p>
  ) : (
    <div>
      {orders.map((order) => {
        const statusToSet = nextStatus[order.status];

        return (
          <article key={order.id}>
            <h3>Order #{order.id}</h3>

            <p>User ID: {order.user_id}</p>

            <p>Status: {order.status}</p>

            <p>
              Created:{" "}
              {new Date(order.created_at).toLocaleString()}
            </p>

            {order.items.map((item) => (
              <div key={item.id}>
                <p>
                  {item.product?.title ??
                    `Product #${item.product_id}`}
                </p>
                <p>Quantity: {item.quantity}</p>
                <p>
                  Unit price: ${item.unit_price.toFixed(2)}
                </p>
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

            {statusToSet && (
              <button
                type="button"
                onClick={() =>
                  handleStatusUpdate(order.id, statusToSet)
                }
                disabled={updatingOrderId === order.id}
              >
                {updatingOrderId === order.id
                  ? "Updating..."
                  : `Mark as ${statusToSet}`}
              </button>
            )}
          </article>
        );
      })}
    </div>
  )}
</section>
);
}
export default AdminOrdersPage;
