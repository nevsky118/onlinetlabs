import "server-only"
import { decodeJwt } from "jose/jwt/decode"
import { getBackendToken } from "./token"

/**
 * Claims the backend puts on the exchange JWT. The source of truth for all of
 * them is the users table, not the better-auth session: better-auth runs on an
 * in-memory adapter here, so anything it reports about a user is unreliable.
 */
type BackendClaims = {
  role?: string
  is_active?: boolean
  can_view_logs?: boolean
}

const NO_CLAIMS: BackendClaims = {}

async function readBackendClaims(): Promise<BackendClaims> {
  const token = await getBackendToken()
  if (!token) return NO_CLAIMS
  try {
    return decodeJwt(token) as BackendClaims
  } catch {
    return NO_CLAIMS
  }
}

export async function getBackendUserRole(): Promise<string | null> {
  const { role } = await readBackendClaims()
  return role ?? null
}

export async function hasInstructorAccess(): Promise<boolean> {
  const role = await getBackendUserRole()
  return role === "instructor" || role === "admin"
}

export async function isBackendUserActive(): Promise<boolean> {
  const { is_active } = await readBackendClaims()
  return is_active === true
}

export async function canViewAgentLogs(): Promise<boolean> {
  const { can_view_logs } = await readBackendClaims()
  return can_view_logs === true
}
