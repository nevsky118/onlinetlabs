import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

export async function POST(req: Request) {
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const body = await req.json()
  const r = await fetch(`${serverEnv.BACKEND_URL}/users/me/consent`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  })

  return new Response(r.body, { status: r.status })
}

export async function DELETE(req: Request) {
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const { searchParams } = new URL(req.url)
  const scope = searchParams.get("scope") ?? ""
  const r = await fetch(
    `${serverEnv.BACKEND_URL}/users/me/consent?scope=${encodeURIComponent(scope)}`,
    { method: "DELETE", headers: { Authorization: `Bearer ${token}` } }
  )

  return new Response(r.body, { status: r.status })
}
