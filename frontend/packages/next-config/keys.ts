import { z } from "zod"

// Cross-domain URLs. Both apps validate the same set.
const schema = z.object({
  NEXT_PUBLIC_WEB_URL: z.url(),
  NEXT_PUBLIC_APP_URL: z.url(),
  NEXT_PUBLIC_AUTH_URL: z.url(),
  NEXT_PUBLIC_WS_BASE_URL: z.string().min(1),
  NEXT_PUBLIC_ANALYTICS_URL: z.url().optional(),
})

export const publicKeys = () =>
  schema.parse({
    NEXT_PUBLIC_WEB_URL: process.env.NEXT_PUBLIC_WEB_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_AUTH_URL: process.env.NEXT_PUBLIC_AUTH_URL,
    NEXT_PUBLIC_WS_BASE_URL: process.env.NEXT_PUBLIC_WS_BASE_URL,
    NEXT_PUBLIC_ANALYTICS_URL: process.env.NEXT_PUBLIC_ANALYTICS_URL,
  })
