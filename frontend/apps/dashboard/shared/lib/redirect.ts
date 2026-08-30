// Same localhost fallback as apps/web/shared/lib/urls.ts, which also holds the real production value
const WEB_ORIGIN = process.env.NEXT_PUBLIC_WEB_URL ?? "http://localhost:3001"

/** Locale is required. Without it the redirect lands on the proxy default locale instead of the user choice. */
export function defaultRedirect(locale: string): string {
  return `/${locale}/sessions`
}

export function validateRedirect(url: string | null, fallback: string): string {
  // "/" carries no destination: treat it as absent so the locale-aware fallback wins.
  if (!url || url === "/") return fallback
  if (url.startsWith("/") && !url.startsWith("//")) return url
  // Absolute URLs pass only on an exact web origin match, anything else is an open redirect
  try {
    return new URL(url).origin === WEB_ORIGIN ? url : fallback
  } catch {
    return fallback
  }
}
