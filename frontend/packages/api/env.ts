import "server-only"
import { z } from "zod"

// Server env, validated when the module loads, failing with a clear error.
const schema = z.object({
  BACKEND_URL: z.string().url(),
  INTERNAL_API_TOKEN: z.string().min(1),
})

export const serverEnv = schema.parse({
  BACKEND_URL: process.env.BACKEND_URL,
  INTERNAL_API_TOKEN: process.env.INTERNAL_API_TOKEN,
})
