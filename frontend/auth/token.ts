import { headers } from "next/headers"
import { backendExchangeToken } from "./api"
import { auth } from "@/auth"

export async function getBackendToken(): Promise<string | null> {
  try {
    const session = await auth.api.getSession({
      headers: await headers(),
    })
    if (!session?.user?.id) return null
    return await backendExchangeToken(session.user.id, session.user.email)
  } catch {
    // Нет сессии / обмен не удался → null; вызывающий получит 401 и покажет not-found, а не 500.
    return null
  }
}
