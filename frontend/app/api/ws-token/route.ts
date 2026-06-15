import { BackendUnavailableError, getBackendToken } from "@/auth/token"

export async function GET() {
  try {
    const token = await getBackendToken()
    if (!token) return new Response("Unauthorized", { status: 401 })
    return Response.json({ token })
  } catch (error) {
    // Транзиентный сбой backend ≠ разлогин: 503, клиент повторит, а не уйдёт на sign-in.
    if (error instanceof BackendUnavailableError) {
      return new Response("Backend unavailable", { status: 503 })
    }
    throw error
  }
}
