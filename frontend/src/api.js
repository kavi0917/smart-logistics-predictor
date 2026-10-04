import axios from "axios";

// Backend URL comes from the VITE_API_URL environment variable (see .env.example) - never hard-coded in components.
export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
export const TOKEN_KEY = "slp_token";

const api = axios.create({ baseURL: API_URL, timeout: 20000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const isLogin = error.config?.url?.includes("/api/auth/login");
    if (error.response?.status === 401 && !isLogin) {
      localStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event("slp-unauthorized"));
    }
    return Promise.reject(error);
  }
);

/** Turn any axios error into a short message that is safe to show to the user. */
export function errorMessage(err) {
  if (!err) return "Something went wrong";
  const data = err.response?.data;
  if (data?.errors?.length) {
    return data.errors.map((e) => `${e.field || "input"}: ${e.message}`).join("; ");
  }
  if (typeof data?.detail === "string") return data.detail;
  if (err.code === "ERR_NETWORK" || !err.response) return "Cannot reach the server. Is the backend running?";
  return "Something went wrong";
}

export default api;
