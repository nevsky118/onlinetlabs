import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

export async function GET() {
  const token = await getBackendToken().catch(() => null)
  if (!token) return Response.json([], { status: 401 })

  const r = await fetch(`${serverEnv.BACKEND_URL}/users/me/sessions`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })
  return Response.json(await r.json(), { status: r.status })
}
