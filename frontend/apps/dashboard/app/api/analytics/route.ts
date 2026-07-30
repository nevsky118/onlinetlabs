import { serverEnv } from "@repo/api/env"
import { getBackendToken } from "@repo/auth/server"

// web posts cross-origin to the dashboard, so preflight and CORS response headers are required
const ALLOWED_ORIGIN = process.env.NEXT_PUBLIC_WEB_URL ?? ""
const corsHeaders = {
  "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Credentials": "true",
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders })
}

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
    return new Response(null, {
      status: upstream.ok ? 204 : upstream.status,
      headers: corsHeaders,
    })
  } catch {
    return new Response(null, { status: 204, headers: corsHeaders }) // fire and forget, never fail the client
  }
}
