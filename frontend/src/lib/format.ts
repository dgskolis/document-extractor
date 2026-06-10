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

export function formatDateOptional(iso: string): string {
  if (!iso) {
    return "Not extracted";
  }

  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) {
    return "Not extracted";
  }

  return formatDate(iso);
}

export function statusBadgeVariant(
  status: OrderStatus,
): "secondary" | "default" | "outline" {
  switch (status) {
    case "pending":
      return "secondary";
    case "processing":
      return "default";
    case "complete":
      return "outline";
  }
}

export function formatStatusLabel(status: OrderStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
