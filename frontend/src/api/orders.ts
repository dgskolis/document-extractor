import { mockOrders } from "../mocks/orders";
import type { Order } from "../types";

export async function getOrders(): Promise<Order[]> {
  // TODO: replace with real API call via apiClient
  return Promise.resolve(mockOrders);
}
