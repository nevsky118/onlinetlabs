import { getBackendToken } from "@/auth/token"

export async function GET() {
  const token = await getBackendToken()
  if (!token) return new Response("Unauthorized", { status: 401 })
  return Response.json({ token })
}
