import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"
import { getBackendToken } from "@repo/auth/server"

export async function GET() {
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const response = await fetch(
    `${serverEnv.BACKEND_URL}/users/me/preferences`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Locale": await getRequestLocale(),
      },
      cache: "no-store",
    }
  )
  return new Response(response.body, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  })
}

export async function PATCH(req: Request) {
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const body = await req.json()
  const response = await fetch(
    `${serverEnv.BACKEND_URL}/users/me/preferences`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        "X-Locale": await getRequestLocale(),
      },
      body: JSON.stringify(body),
    }
  )
  return new Response(response.body, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  })
}
