// Caddy appends the real peer last, so read the last entry.
const TRUSTED_PROXY_HOPS = 1

// The caller's own address, or null when none was forwarded.
export function readClientAddress(
  callerHeaders: Headers | null | undefined
): string | null {
  const forwarded = callerHeaders?.get("x-forwarded-for") ?? ""
  const hops = forwarded
    .split(",")
    .map((hop) => hop.trim())
    .filter(Boolean)
  return hops.at(-TRUSTED_PROXY_HOPS) ?? null
}

// The header that carries that address to the backend.
export function forwardClientAddress(
  callerHeaders: Headers | null | undefined
): Record<string, string> {
  const address = readClientAddress(callerHeaders)
  return address ? { "X-Forwarded-For": address } : {}
}
