import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

export async function POST(req: Request) {
  const body = await req.text()
  const token = await getBackendToken().catch(() => null)

  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (token) headers["Authorization"] = `Bearer ${token}`

  try {
    const upstream = await fetch(`${serverEnv.BACKEND_URL}/analytics/events`, {
      method: "POST",
      headers,
      body,
    })
    return new Response(null, { status: upstream.ok ? 204 : upstream.status })
  } catch {
    return new Response(null, { status: 204 }) // шлём и забываем, клиента не валим
  }
}
