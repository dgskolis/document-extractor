export type OrderStatus = "pending" | "processing" | "complete";

export interface Order {
  id: string;
  patient_first_name: string;
  patient_last_name: string;
  date_of_birth: string;
  status: OrderStatus;
  created_at: string;
}

export interface OrderCreateInput {
  patient_first_name: string;
  patient_last_name: string;
  date_of_birth: string;
}

export interface OrderUpdateInput {
  patient_first_name?: string;
  patient_last_name?: string;
  date_of_birth?: string;
  status?: OrderStatus;
}

export interface ExtractedPatient {
  patient_first_name: string;
  patient_last_name: string;
  date_of_birth: string;
}
