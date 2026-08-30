import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"

/**
 * Proxies the one-time GNS3 ticket redemption. Deliberately unauthenticated:
 * the ticket itself is the credential, so the relay page can redeem it without
 * a dashboard session. Rate limiting lives on the backend route.
 */
export async function POST(request: Request) {
  const body = await request.json().catch(() => null)
  if (typeof body?.ticket !== "string" || body.ticket.length === 0) {
    return Response.json({ code: "error.request.invalid" }, { status: 400 })
  }

  const backendResponse = await fetch(`${serverEnv.BACKEND_URL}/gns3/redeem`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Locale": await getRequestLocale(),
    },
    body: JSON.stringify({ ticket: body.ticket }),
    cache: "no-store",
  })

  return new Response(backendResponse.body, {
    status: backendResponse.status,
    headers: { "Content-Type": "application/json" },
  })
}
