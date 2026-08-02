import "server-only"

import { type Locale, routing } from "@repo/i18n/routing"
import { cookies, headers } from "next/headers"

function isLocale(value: string | undefined): value is Locale {
  return !!value && (routing.locales as readonly string[]).includes(value)
}

/** Locale for a server-side backend call: NEXT_LOCALE cookie, then accept-language, then the default. */
export async function getRequestLocale(): Promise<Locale> {
  const fromCookie = (await cookies()).get("NEXT_LOCALE")?.value
  if (isLocale(fromCookie)) return fromCookie

  const accept = (await headers()).get("accept-language") ?? ""
  for (const tag of accept.split(",")) {
    const base = tag.split(";")[0]?.trim().split("-")[0]?.toLowerCase()
    if (isLocale(base)) return base
  }
  return routing.defaultLocale
}
