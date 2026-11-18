
import axios from "axios";

const API_URL = "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach the JWT token automatically to protected requests.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("insidershield_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// If the backend rejects authentication, clear the expired session.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("insidershield_token");
      localStorage.removeItem("insidershield_user");
      window.location.reload();
    }

    return Promise.reject(error);
  }
);

export default api;
