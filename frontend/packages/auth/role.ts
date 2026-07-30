import "server-only"

import { decodeJwt } from "jose/jwt/decode"
import { getBackendToken } from "./token"

// The source of truth for the role is the backend (the users table), not the
// better-auth session. better-auth runs on an in-memory adapter here, so the
// role in the session is not reliable. The backend-JWT issued by /auth/exchange
// carries the role claim from the database.
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

export async function canViewAgentLogs(): Promise<boolean> {
  const token = await getBackendToken()
  if (!token) return false
  try {
    const payload = decodeJwt(token) as { can_view_logs?: boolean }
    return payload.can_view_logs === true
  } catch {
    return false
  }
}
