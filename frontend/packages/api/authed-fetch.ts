import "server-only"

import { headers } from "next/headers"
import { RedirectType, redirect } from "next/navigation"
import { serverEnv } from "./env"
import { getRequestLocale } from "./request-locale"

type MissingTokenBehavior = "redirect" | "throw"

/** Token arrives via factory because a direct import of the auth package would create a cycle. */
export function createAuthedFetch(
  getToken: () => Promise<string | null>,
  opts: { onMissingToken?: MissingTokenBehavior } = {}
) {
  const onMissing = opts.onMissingToken ?? "redirect"

  return async function authedFetch(
    path: string,
    init?: RequestInit
  ): Promise<Response> {
    const token = await getToken()
    if (!token) {
      if (onMissing === "throw") return new Response(null, { status: 401 })
      // No backend token means no session or an orphaned one. Redirect to sign-in instead of an opaque 500.
      // Uses replace since a signed-out user cannot return to the protected page anyway.
      const referer = (await headers()).get("referer")
      const returnTo = referer
        ? new URL(referer).pathname + new URL(referer).search
        : "/"
      redirect(
        `/sign-in?redirect=${encodeURIComponent(returnTo)}`,
        RedirectType.replace
      )
    }
    const locale = await getRequestLocale()
    return fetch(`${serverEnv.BACKEND_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "X-Locale": locale,
        ...(init?.headers || {}),
      },
      cache: "no-store",
    })
  }
}
