import { auth } from "@repo/auth/server"
import { toNextJsHandler } from "better-auth/next-js"

const handlers = toNextJsHandler(auth)

// web reads the session cross-origin. Without CORS headers the browser blocks the response.
const ALLOWED_ORIGIN = process.env.NEXT_PUBLIC_WEB_URL ?? ""

function withCors(res: Response, origin: string | null): Response {
  if (!origin || origin !== ALLOWED_ORIGIN) return res
  res.headers.set("Access-Control-Allow-Origin", origin)
  res.headers.set("Access-Control-Allow-Credentials", "true")
  res.headers.set("Vary", "Origin")
  return res
}

export async function OPTIONS(req: Request) {
  const origin = req.headers.get("origin")
  if (!origin || origin !== ALLOWED_ORIGIN)
    return new Response(null, { status: 204 })
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Allow-Credentials": "true",
      Vary: "Origin",
    },
  })
}

export async function GET(req: Request) {
  return withCors(await handlers.GET(req), req.headers.get("origin"))
}

export async function POST(req: Request) {
  return withCors(await handlers.POST(req), req.headers.get("origin"))
}
