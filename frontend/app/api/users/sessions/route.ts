import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

export async function GET() {
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const r = await fetch(`${serverEnv.BACKEND_URL}/users/me/sessions`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })
  return new Response(r.body, {
    status: r.status,
    headers: { "Content-Type": "application/json" },
  })
}

export async function DELETE() {
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const r = await fetch(`${serverEnv.BACKEND_URL}/users/me/sessions`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  })
  return new Response(r.body, {
    status: r.status,
    headers: { "Content-Type": "application/json" },
  })
}
