import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"
import { getBackendToken } from "@repo/auth/server"

export async function GET() {
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const upstream = await fetch(`${serverEnv.BACKEND_URL}/chat/models`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Locale": await getRequestLocale(),
    },
    cache: "no-store",
  })

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type":
        upstream.headers.get("Content-Type") ?? "application/json",
    },
  })
}
