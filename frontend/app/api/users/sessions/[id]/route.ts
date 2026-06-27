import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = await getBackendToken().catch(() => null)
  if (!token) return new Response("Unauthorized", { status: 401 })

  const { id } = await params
  const r = await fetch(
    `${serverEnv.BACKEND_URL}/users/me/sessions/${encodeURIComponent(id)}`,
    { method: "DELETE", headers: { Authorization: `Bearer ${token}` } }
  )
  return new Response(r.body, {
    status: r.status,
    headers: { "Content-Type": "application/json" },
  })
}
