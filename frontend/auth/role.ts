import "server-only"

import { decodeJwt } from "jose/jwt/decode"
import { getBackendToken } from "./token"

// Источник правды о роли — backend (таблица users), а не better-auth сессия:
// better-auth здесь работает на in-memory адаптере и роль в сессии недостоверна.
// Backend-JWT, выданный /auth/exchange, несёт claim role из БД.
export async function getBackendUserRole(): Promise<string | null> {
  const token = await getBackendToken()
  if (!token) return null
  try {
    const payload = decodeJwt(token) as { role?: string }
    return payload.role ?? null
  } catch {
    return null
  }
}

export async function hasInstructorAccess(): Promise<boolean> {
  const role = await getBackendUserRole()
  return role === "instructor" || role === "admin"
}
