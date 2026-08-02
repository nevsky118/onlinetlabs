import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"
import { getBackendToken } from "@repo/auth/server"

export async function GET() {
  const token = await getBackendToken().catch(() => null)
  if (!token) return Response.json([], { status: 401 })

  const r = await fetch(`${serverEnv.BACKEND_URL}/users/me/sessions`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Locale": await getRequestLocale(),
    },
    cache: "no-store",
  })
  return Response.json(await r.json(), { status: r.status })
}
