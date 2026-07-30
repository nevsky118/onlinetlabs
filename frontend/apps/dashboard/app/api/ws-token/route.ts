import { BackendUnavailableError, getBackendToken } from "@repo/auth/server"

export async function GET() {
  try {
    const token = await getBackendToken()
    if (!token) return new Response("Unauthorized", { status: 401 })
    return Response.json({ token })
  } catch (error) {
    // A transient backend failure ≠ a logout. 503, the client will retry instead of leaving for sign-in.
    if (error instanceof BackendUnavailableError) {
      return new Response("Backend unavailable", { status: 503 })
    }
    throw error
  }
}
