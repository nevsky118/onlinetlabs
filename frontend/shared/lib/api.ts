import axios from "axios"

export const api = axios.create({
  baseURL: process.env.BACKEND_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
})
