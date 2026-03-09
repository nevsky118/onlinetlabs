import { decodeJwt as joseDecodeJwt } from "jose/jwt/decode"

/**
 * Backend JWT payload structure
 */
interface BackendJWTPayload {
  readonly token_type: string
  readonly exp: number
  readonly iat: number
  readonly jti: string
  readonly user_id: number
  readonly user_type: string
  readonly permission_group: string[]
}

/**
 * JWT payload structure (normalized)
 */
export interface DecodedToken {
  readonly exp: number // Unix timestamp (seconds)
  readonly iat: number // Issued at
  readonly sub: string // User ID (mapped from user_id)
  readonly jti?: string // JWT ID
}

/**
 * Type-safe JWT decoder
 * No verification - only for reading expiry
 * Handles backend JWT structure with user_id instead of sub
 */
export function decodeJwt(token: string): DecodedToken {
  try {
    const payload = joseDecodeJwt(token) as unknown as BackendJWTPayload

    if (!payload.exp || !payload.iat) {
      throw new Error("Missing required JWT claims (exp, iat)")
    }

    // Backend uses user_id instead of standard sub claim
    const userId = payload.user_id.toString()

    if (!userId) {
      throw new Error("Missing user identifier (user_id or sub)")
    }

    return {
      exp: payload.exp,
      iat: payload.iat,
      sub: userId,
      jti: payload.jti,
    } satisfies DecodedToken
  } catch {
    throw new Error("Failed to decode JWT")
  }
}

/**
 * Check if token is expired
 */
export function isTokenExpired(expiresAt: number): boolean {
  const now = Math.floor(Date.now() / 1000) // Current time in seconds
  return now >= expiresAt
}

/**
 * Check if token expires soon (within buffer time)
 */
export function isTokenExpiringSoon(
  expiresAt: number,
  bufferSeconds: number = 5 * 60 // 5 minutes default
): boolean {
  const now = Math.floor(Date.now() / 1000)
  return now >= expiresAt - bufferSeconds
}
