import { headers } from "next/headers"
import { backendExchangeToken } from "./api"
import { auth } from "@/shared/auth"

export async function getBackendToken(): Promise<string | null> {
  const session = await auth.api.getSession({
    headers: await headers(),
  })

  if (!session?.user?.id) return null

  try {
    return await backendExchangeToken(session.user.id, session.user.email)
  } catch {
    return null
  }
}
