import apiClient, { isApiError } from "./client";
import {
  GENERIC_UPLOAD_ERROR_MESSAGE,
  UploadDocumentError,
} from "./upload-errors";
import type {
  ExtractedPatient,
  Order,
  OrderCreateInput,
  OrderStatus,
  OrderUpdateInput,
} from "../types";

interface BackendOrder {
  id: string;
  patient_first_name: string;
  patient_last_name: string;
  date_of_birth: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

interface BackendOrderListResponse {
  items: BackendOrder[];
  total: number;
  limit: number;
  offset: number;
}

interface BackendExtraction {
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
}

interface BackendDocumentUploadResponse {
  extraction: BackendExtraction;
}

interface BackendUploadErrorResponse {
  error?: string;
  reference_id?: string;
  extraction?: BackendExtraction;
}

function mapStatus(status: string): OrderStatus {
  switch (status) {
    case "in_progress":
      return "processing";
    case "completed":
      return "complete";
    case "pending":
      return "pending";
    case "processing":
      return "processing";
    case "complete":
      return "complete";
    default:
      return "pending";
  }
}

function mapOrder(raw: BackendOrder): Order {
  return {
    id: String(raw.id),
    patient_first_name: raw.patient_first_name,
    patient_last_name: raw.patient_last_name,
    date_of_birth: raw.date_of_birth,
    status: mapStatus(raw.status),
    created_at: raw.created_at,
  };
}

function mapExtraction(raw: BackendExtraction): ExtractedPatient {
  return {
    patient_first_name: raw.first_name ?? "",
    patient_last_name: raw.last_name ?? "",
    date_of_birth: raw.date_of_birth ?? "",
  };
}

function mapUpdatePayload(data: OrderUpdateInput): Record<string, unknown> {
  const payload: Record<string, unknown> = {};

  if (data.patient_first_name !== undefined) {
    payload.patient_first_name = data.patient_first_name;
  }
  if (data.patient_last_name !== undefined) {
    payload.patient_last_name = data.patient_last_name;
  }
  if (data.date_of_birth !== undefined) {
    payload.date_of_birth = data.date_of_birth;
  }
  if (data.status !== undefined) {
    payload.status =
      data.status === "processing"
        ? "in_progress"
        : data.status === "complete"
          ? "completed"
          : data.status;
  }

  return payload;
}

function parseUploadErrorResponse(data: unknown): UploadDocumentError {
  const payload = (data ?? {}) as BackendUploadErrorResponse;
  const partialPatient = payload.extraction
    ? mapExtraction(payload.extraction)
    : null;
  const referenceId =
    typeof payload.reference_id === "string" ? payload.reference_id : null;

  return new UploadDocumentError(partialPatient, referenceId);
}

export async function getOrders(): Promise<Order[]> {
  const { data } = await apiClient.get<BackendOrderListResponse>("/api/v1/orders");
  return data.items.map(mapOrder);
}

export async function getOrder(id: string): Promise<Order> {
  const { data } = await apiClient.get<BackendOrder>(`/api/v1/orders/${id}`);
  return mapOrder(data);
}

export async function createOrder(input: OrderCreateInput): Promise<Order> {
  const { data } = await apiClient.post<BackendOrder>("/api/v1/orders", input);
  return mapOrder(data);
}

export async function updateOrder(
  id: string,
  input: OrderUpdateInput,
): Promise<Order> {
  const { data } = await apiClient.put<BackendOrder>(
    `/api/v1/orders/${id}`,
    mapUpdatePayload(input),
  );
  return mapOrder(data);
}

export async function deleteOrder(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/orders/${id}`);
}

export async function uploadDocument(file: File): Promise<ExtractedPatient> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const { data } = await apiClient.post<BackendDocumentUploadResponse>(
      "/api/v1/orders/upload-document",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );

    return mapExtraction(data.extraction);
  } catch (error) {
    const responseData = isApiError(error) ? error.responseData : undefined;
    if (responseData && typeof responseData === "object") {
      const payload = responseData as BackendUploadErrorResponse;
      if (payload.reference_id || payload.extraction) {
        throw parseUploadErrorResponse(payload);
      }
    }

    throw new UploadDocumentError(null, null);
  }
}

export { GENERIC_UPLOAD_ERROR_MESSAGE, mapExtraction };
