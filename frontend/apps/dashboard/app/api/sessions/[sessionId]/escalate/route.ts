import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"
import { getBackendToken } from "@repo/auth/server"

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  const { sessionId } = await params
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const r = await fetch(
    `${serverEnv.BACKEND_URL}/users/me/sessions/${sessionId}/escalate`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Locale": await getRequestLocale(),
      },
    }
  )

  return new Response(r.body, { status: r.status })
}
