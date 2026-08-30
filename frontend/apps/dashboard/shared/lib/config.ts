export const webUrl = process.env.NEXT_PUBLIC_WEB_URL ?? "http://localhost:3001"

export const siteConfig = {
  url: "#",
  ogImage: "#",
  links: {
    github: "https://github.com/",
  },
  author: "",
}

/**
 * Nav items depend on translations and locale, so this is a function rather than a module-level array.
 * Locale is baked into href because the result feeds both Link consumers and router.push.
 */
export function getNavItems(t: (key: string) => string, locale: string) {
  return [
    { href: `${webUrl}/${locale}/courses`, label: t("navCourses") },
    { href: `${webUrl}/${locale}/labs`, label: t("navLabs") },
    { href: `/${locale}/sessions`, label: t("navMySessions") },
  ]
}

/** Static section list for CommandMenu and MobileNav. */
export function getDashboardDestinations(
  t: (key: string) => string,
  locale: string
) {
  return [
    { name: t("mySessions"), href: `/${locale}/sessions` },
    { name: t("settings"), href: `/${locale}/settings` },
    { name: t("instructorCabinet"), href: `/${locale}/instructor` },
    { name: t("admin"), href: `/${locale}/admin` },
  ]
}
