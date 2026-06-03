import { useEffect, useState } from "react";

import { getOrders } from "../api/orders";
import type { Order } from "../types";

export function useOrders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getOrders()
      .then(setOrders)
      .catch(() => setError("Failed to load orders"))
      .finally(() => setLoading(false));
  }, []);

  return { orders, loading, error };
}
