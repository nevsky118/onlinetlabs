const DEFAULT_REDIRECT = "/"

export function validateRedirect(
  url: string | null,
  fallback = DEFAULT_REDIRECT
): string {
  if (!url) return fallback
  if (!url.startsWith("/") || url.startsWith("//")) return fallback
  return url
}
