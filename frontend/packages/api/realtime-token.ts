async function fetchToken(url: string): Promise<string> {
  const response = await fetch(url)
  if (!response.ok) throw new Error("token fetch failed")
  const { token } = (await response.json()) as { token: string }
  return token
}

export function fetchBackendToken(): Promise<string> {
  return fetchToken("/api/auth/backend-token")
}

export function fetchWsToken(): Promise<string> {
  return fetchToken("/api/ws-token")
}
