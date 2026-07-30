import { defineRouting } from "next-intl/routing"

// Prefix is always present. /ru and /en stay symmetric with no hidden default.
export const routing = defineRouting({
  locales: ["ru", "en"],
  // An unknown Accept-Language lands on the English version.
  defaultLocale: "en",
  localePrefix: "always",
})

export type Locale = (typeof routing.locales)[number]
