async function fetchToken(url: string): Promise<string> {
  const r = await fetch(url)
  if (!r.ok) throw new Error("token fetch failed")
  const { token } = (await r.json()) as { token: string }
  return token
}

export function fetchBackendToken(): Promise<string> {
  return fetchToken("/api/auth/backend-token")
}

export function fetchWsToken(): Promise<string> {
  return fetchToken("/api/ws-token")
}
