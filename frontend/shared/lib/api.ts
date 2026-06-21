import axios from "axios"
import { serverEnv } from "@/lib/env"

export const api = axios.create({
  baseURL: serverEnv.BACKEND_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
})
