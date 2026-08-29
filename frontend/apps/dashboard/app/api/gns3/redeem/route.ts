import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"

export async function POST(req: Request) {
  const body = await req.json()

  const r = await fetch(`${serverEnv.BACKEND_URL}/gns3/redeem`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Locale": await getRequestLocale(),
    },
    body: JSON.stringify(body),
    cache: "no-store",
  })

  return new Response(r.body, {
    status: r.status,
    headers: { "Content-Type": "application/json" },
  })
}
