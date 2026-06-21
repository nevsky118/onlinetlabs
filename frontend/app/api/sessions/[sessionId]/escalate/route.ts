import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  const { sessionId } = await params
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const r = await fetch(
    `${serverEnv.BACKEND_URL}/users/me/sessions/${sessionId}/escalate`,
    { method: "POST", headers: { Authorization: `Bearer ${token}` } }
  )

  return new Response(r.body, { status: r.status })
}
