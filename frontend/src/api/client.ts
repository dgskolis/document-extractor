import axios, { isAxiosError } from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

apiClient.interceptors.request.use((config) => {
  const apiKey = import.meta.env.VITE_API_KEY;
  if (apiKey) {
    config.headers.set("X-API-Key", apiKey);
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = getApiErrorMessage(error);
    const isNetworkError =
      isAxiosError(error) &&
      (!error.response ||
        error.code === "ERR_NETWORK" ||
        error.message === "Network Error");

    return Promise.reject(
      new ApiError(
        message,
        isNetworkError,
        error.response?.data,
        error.response?.status,
      ),
    );
  },
);

export class ApiError extends Error {
  readonly isNetworkError: boolean;
  readonly responseData: unknown;
  readonly statusCode: number | undefined;

  constructor(
    message: string,
    isNetworkError = false,
    responseData: unknown = undefined,
    statusCode: number | undefined = undefined,
  ) {
    super(message);
    this.name = "ApiError";
    this.isNetworkError = isNetworkError;
    this.responseData = responseData;
    this.statusCode = statusCode;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function isNetworkError(error: unknown): boolean {
  return isApiError(error) && error.isNetworkError;
}

export function getApiErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.message;
  }

  if (isAxiosError(error)) {
    const apiError = error.response?.data?.error;
    if (typeof apiError === "string" && apiError.length > 0) {
      return apiError;
    }
    if (error.message) {
      return error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed";
}

export default apiClient;
