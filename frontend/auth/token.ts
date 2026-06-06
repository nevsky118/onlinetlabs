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
    // Нет сессии (getSession бросает Unauthorized), либо обмен токена не удался —
    // отдаём null. Вызывающий код получит 401 от бэкенда и обработает штатно
    // (страница сессии покажет not-found, а не 500).
    return null
  }
}
