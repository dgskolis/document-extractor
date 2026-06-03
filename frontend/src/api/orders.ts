import { mockOrders } from "../mocks/orders";
import type {
  ExtractedPatient,
  Order,
  OrderCreateInput,
} from "../types";

export async function getOrders(): Promise<Order[]> {
  // TODO: replace with real API call via apiClient
  return Promise.resolve(mockOrders);
}

export async function createOrder(input: OrderCreateInput): Promise<Order> {
  console.log("createOrder", input);
  await new Promise((resolve) => setTimeout(resolve, 300));

  return {
    id: `ord-${Date.now()}`,
    patient_first_name: input.patient_first_name,
    patient_last_name: input.patient_last_name,
    date_of_birth: input.date_of_birth,
    status: "pending",
    created_at: new Date().toISOString(),
  };
}

export async function uploadDocument(file: File): Promise<ExtractedPatient> {
  console.log("uploadDocument", file.name);
  await new Promise((resolve) => setTimeout(resolve, 2000));

  return {
    patient_first_name: "Alex",
    patient_last_name: "Taylor",
    date_of_birth: "1988-09-12",
  };
}
