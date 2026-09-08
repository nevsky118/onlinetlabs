import { forwardClientAddress } from "@repo/api/client-address"
import { serverEnv } from "@repo/api/env"
import { api } from "@repo/api/http"

export interface BackendUser {
  id: string
  email: string
  name: string | null
  image: string | null
  role: string
}

interface TokenResponse {
  access_token: string
  token_type: string
}

// The learner's address, vouched for by the internal token.
function relayHeaders(callerHeaders?: Headers | null): Record<string, string> {
  return {
    Authorization: `Bearer ${serverEnv.INTERNAL_API_TOKEN}`,
    ...forwardClientAddress(callerHeaders),
  }
}

export async function backendLogin(
  email: string,
  password: string,
  callerHeaders?: Headers | null
) {
  const { data } = await api.post<BackendUser>(
    "/auth/login",
    { email, password },
    { headers: relayHeaders(callerHeaders) }
  )
  return data
}

export async function backendRegister(
  email: string,
  password: string,
  name?: string,
  callerHeaders?: Headers | null
) {
  const { data } = await api.post<BackendUser>(
    "/auth/register",
    { email, password, name },
    { headers: relayHeaders(callerHeaders) }
  )
  return data
}

export async function backendUpsertGithubUser(user: {
  email: string
  name: string
  image: string | null | undefined
  provider_account_id: string
}) {
  // Server-only — forward the shared internal token so backend accepts this as a
  // trusted Next.js call. github-callback is server-to-server only.
  const internalToken = process.env.INTERNAL_API_TOKEN
  const { data } = await api.post<BackendUser>(
    "/auth/github-callback",
    user,
    internalToken
      ? { headers: { Authorization: `Bearer ${internalToken}` } }
      : undefined
  )
  return data
}

export async function backendExchangeToken(userId: string, email: string) {
  // Server-only — frontend forwards the shared internal token so backend can
  // distinguish a trusted Next.js call from an arbitrary browser request.
  const internalToken = process.env.INTERNAL_API_TOKEN
  const { data } = await api.post<TokenResponse>(
    "/auth/exchange",
    { user_id: userId, email },
    internalToken
      ? { headers: { Authorization: `Bearer ${internalToken}` } }
      : undefined
  )
  return data.access_token
}
