import "server-only"
import { z } from "zod"

// Серверный env: валидируется при загрузке модуля, падает с ясной ошибкой.
const schema = z.object({
  BACKEND_URL: z.string().url(),
  INTERNAL_API_TOKEN: z.string().min(1),
})

export const serverEnv = schema.parse({
  BACKEND_URL: process.env.BACKEND_URL,
  INTERNAL_API_TOKEN: process.env.INTERNAL_API_TOKEN,
})
