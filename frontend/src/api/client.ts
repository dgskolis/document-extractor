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
    return Promise.reject(new Error(getApiErrorMessage(error)));
  },
);

export function getApiErrorMessage(error: unknown): string {
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
