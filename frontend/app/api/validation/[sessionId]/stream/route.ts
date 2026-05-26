import { getBackendToken } from "@/auth/token"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

/** SSE-прокси: проброс на backend POST /labs/{slug}/sessions/{sid}/validate с Bearer. */
export async function POST(
  req: Request,
  ctx: { params: Promise<{ sessionId: string }> }
) {
  const { sessionId } = await ctx.params
  const tokenPromise = getBackendToken()
  const bodyPromise = req.json() as Promise<{ slug: string }>

  const token = await tokenPromise
  if (!token) return new Response("Unauthorized", { status: 401 })

  const { slug } = await bodyPromise
  if (!slug) return new Response("Missing slug", { status: 400 })

  const upstream = await fetch(
    `${BACKEND_URL}/labs/${slug}/sessions/${sessionId}/validate`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    }
  )

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
