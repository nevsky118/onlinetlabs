import { z } from "zod"

// Client env (NEXT_PUBLIC_*, inlined at build time).
const schema = z.object({
  NEXT_PUBLIC_WS_BASE_URL: z.string().url(),
  NEXT_PUBLIC_APP_URL: z.string().url(),
})

export const clientEnv = schema.parse({
  NEXT_PUBLIC_WS_BASE_URL: process.env.NEXT_PUBLIC_WS_BASE_URL,
  NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
})
