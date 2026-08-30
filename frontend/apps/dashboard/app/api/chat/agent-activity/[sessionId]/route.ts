import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"
import { getBackendToken } from "@repo/auth/server"

export async function GET(
  req: Request,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  const { sessionId } = await params
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const url = new URL(req.url)
  const since = url.searchParams.get("since")
  const limit = url.searchParams.get("limit")

  const upstream = new URL(
    `${serverEnv.BACKEND_URL}/sessions/${sessionId}/agent-activity`
  )
  if (since) upstream.searchParams.set("since", since)
  if (limit) upstream.searchParams.set("limit", limit)

  const response = await fetch(upstream.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Locale": await getRequestLocale(),
    },
    cache: "no-store",
  })

  return new Response(response.body, {
    status: response.status,
    headers: {
      "Content-Type":
        response.headers.get("Content-Type") ?? "application/json",
    },
  })
}
