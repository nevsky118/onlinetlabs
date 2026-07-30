import axios from "axios"
import { headers } from "next/headers"
import { backendExchangeToken } from "./api"
import { auth } from "./betterauth"

/**
 * Transient token exchange failure (429 / 5xx / network). Distinguished from
 * "no session". null takes the user to sign-in, this error goes to 503 / error
 * boundary. Without that distinction any brief backend failure would log the
 * user out.
 */
export class BackendUnavailableError extends Error {
  constructor(public readonly reason?: unknown) {
    super("backend token exchange failed")
    this.name = "BackendUnavailableError"
  }
}

interface CachedToken {
  token: string
  expiresAtMs: number
}

// Backend-JWT cache keyed by better-auth userId. The token lives 5 min, so a
// re-exchange happens about once every 4 min per user, not "before every
// request". The module-level cache only lives within a Next instance. When
// scaling horizontally, replace the storage with Redis. The get/set interface
// is localized here.
const tokenCache = new Map<string, CachedToken>()

// Single-flight. Collapses parallel exchanges (strict-mode duplicates, a burst
// of ws-token + backend-token + chat in one tick) into one network call per user.
const inflight = new Map<string, Promise<string | null>>()

// Refresh 60s before expiry so we never hand out a token that expires in flight.
const REFRESH_SKEW_MS = 60_000

function decodeExpiryMs(jwt: string): number {
  const payload = jwt.split(".")[1]
  const decoded = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"))
  return decoded.exp * 1000
}

export async function getBackendToken(): Promise<string | null> {
  const session = await auth.api.getSession({ headers: await headers() })
  // No better-auth session → null. The caller takes the user to sign-in.
  if (!session?.user?.id) return null

  const userId = session.user.id

  const cached = tokenCache.get(userId)
  if (cached && cached.expiresAtMs - REFRESH_SKEW_MS > Date.now()) {
    return cached.token
  }

  const existing = inflight.get(userId)
  if (existing) return existing

  const exchange = (async (): Promise<string | null> => {
    try {
      const token = await backendExchangeToken(
        session.user.id,
        session.user.email
      )
      tokenCache.set(userId, { token, expiresAtMs: decodeExpiryMs(token) })
      return token
    } catch (error) {
      // 401 = orphaned cookie / no such user on the backend → null → sign-in.
      // Everything else (429 / 5xx / network) = transient → do not log out.
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        return null
      }
      throw new BackendUnavailableError(error)
    } finally {
      inflight.delete(userId)
    }
  })()

  inflight.set(userId, exchange)
  return exchange
}
