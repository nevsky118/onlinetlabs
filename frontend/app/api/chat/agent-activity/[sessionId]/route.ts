import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

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

  const r = await fetch(upstream.toString(), {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })

  return new Response(r.body, {
    status: r.status,
    headers: {
      "Content-Type": r.headers.get("Content-Type") ?? "application/json",
    },
  })
}
