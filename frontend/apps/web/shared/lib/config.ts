import type { getTranslations } from "next-intl/server"
import { appUrl } from "./urls"

export const siteConfig = {
  url: "#",
  ogImage: "#",
  links: {
    github: "https://github.com/",
  },
  author: "",
}

type NavT = Awaited<ReturnType<typeof getTranslations>>

/**
 * A function rather than a module constant because nav items depend on translations and locale.
 * Locale is baked into href. Consumers differ (Link, router.push) and MobileNav mixes in localized fumadocs paths.
 */
export function getNavItems(t: NavT, locale: string) {
  return [
    {
      href: `/${locale}/courses`,
      label: t("courses"),
    },
    {
      href: `/${locale}/labs`,
      label: t("labs"),
    },
    {
      // Cross-domain link, this entry lives in the dashboard
      href: `${appUrl}/${locale}/sessions`,
      label: t("mySessions"),
    },
  ]
}
