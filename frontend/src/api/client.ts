import axios from "axios";

export const api = axios.create({ baseURL: "/api", withCredentials: true });

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401 && onUnauthorized) onUnauthorized();
    return Promise.reject(error);
  },
);

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (error.response?.status === 403) return "No tienes permisos para esta acción";
    if (error.response?.status === 422) return "Revisa los campos del formulario";
  }
  return "Ocurrió un error inesperado";
}
