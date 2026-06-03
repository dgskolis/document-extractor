import type { Order } from "../types";

export const mockOrders: Order[] = [
  {
    id: "ord-001",
    patient_first_name: "Jane",
    patient_last_name: "Smith",
    date_of_birth: "1985-03-14",
    status: "complete",
    created_at: "2026-05-28T10:15:00Z",
  },
  {
    id: "ord-002",
    patient_first_name: "Michael",
    patient_last_name: "Johnson",
    date_of_birth: "1972-11-02",
    status: "processing",
    created_at: "2026-05-29T14:30:00Z",
  },
  {
    id: "ord-003",
    patient_first_name: "Emily",
    patient_last_name: "Davis",
    date_of_birth: "1990-07-21",
    status: "pending",
    created_at: "2026-06-01T09:00:00Z",
  },
  {
    id: "ord-004",
    patient_first_name: "Robert",
    patient_last_name: "Wilson",
    date_of_birth: "1968-01-09",
    status: "pending",
    created_at: "2026-06-02T16:45:00Z",
  },
  {
    id: "ord-005",
    patient_first_name: "Sarah",
    patient_last_name: "Brown",
    date_of_birth: "1995-12-30",
    status: "processing",
    created_at: "2026-06-03T08:20:00Z",
  },
];
