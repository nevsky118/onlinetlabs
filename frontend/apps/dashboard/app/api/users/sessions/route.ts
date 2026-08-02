import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"
import { getBackendToken } from "@repo/auth/server"

export async function GET() {
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const r = await fetch(`${serverEnv.BACKEND_URL}/users/me/auth-sessions`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Locale": await getRequestLocale(),
    },
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

  const r = await fetch(`${serverEnv.BACKEND_URL}/users/me/auth-sessions`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Locale": await getRequestLocale(),
    },
  })
  return new Response(r.body, {
    status: r.status,
    headers: { "Content-Type": "application/json" },
  })
}
