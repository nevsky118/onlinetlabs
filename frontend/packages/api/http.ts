import axios from "axios"
import { serverEnv } from "./env"

export const api = axios.create({
  baseURL: serverEnv.BACKEND_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
})
