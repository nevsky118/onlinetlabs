import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"
import { getBackendToken } from "@repo/auth/server"

/** SSE proxy. Forwards the body to backend /chat/stream + Bearer. Forwarding Content-Type is critical for AI SDK stream parsing. */
export async function POST(req: Request) {
  const tokenPromise = getBackendToken()
  const bodyPromise = req.text()
  const localePromise = getRequestLocale()

  const token = await tokenPromise
  if (!token) return new Response("Unauthorized", { status: 401 })

  const body = await bodyPromise
  const upstream = await fetch(`${serverEnv.BACKEND_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Locale": await localePromise,
    },
    body,
  })

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type":
        upstream.headers.get("Content-Type") ?? "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  })
}
