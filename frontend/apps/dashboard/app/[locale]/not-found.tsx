import { routing } from "@repo/i18n/routing"
import { hasLocale } from "next-intl"
import { getLocale, getTranslations } from "next-intl/server"
import Link from "next/link"

export default async function NotFound() {
  const requested = await getLocale()
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.notFound",
  })

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">{t("heading")}</h1>
      <p className="text-muted-foreground">{t("description")}</p>
      <Link
        href={`/${locale}`}
        className="rounded-none bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
      >
        {t("home")}
      </Link>
    </div>
  )
}
