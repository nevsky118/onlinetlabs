import { getBackendToken } from "@/auth/token"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

export async function GET() {
  const token = await getBackendToken().catch(() => null)
  if (!token) return Response.json([], { status: 401 })

  const r = await fetch(`${BACKEND_URL}/users/me/sessions`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })
  return Response.json(await r.json(), { status: r.status })
}
