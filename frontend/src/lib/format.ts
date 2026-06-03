import type { Order, OrderStatus } from "@/types";

export function formatPatientName(order: Order): string {
  return `${order.patient_last_name}, ${order.patient_first_name}`;
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric",
  }).format(new Date(iso));
}

export function statusBadgeClass(status: OrderStatus): string {
  switch (status) {
    case "pending":
      return "bg-gray-100 text-gray-700 hover:bg-gray-100";
    case "processing":
      return "bg-blue-100 text-blue-700 hover:bg-blue-100";
    case "complete":
      return "bg-green-100 text-green-700 hover:bg-green-100";
  }
}

export function formatStatusLabel(status: OrderStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
