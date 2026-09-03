import axios from "axios";

// Standard axios instance for JalRakshak API
export const client = axios.create({
  baseURL: "/api/v1", // Will proxy in Vite
  headers: {
    "Content-Type": "application/json",
  },
});

export const apiClient = client;
