import { routing } from "@repo/i18n/routing"
import { notFound } from "next/navigation"
import { hasLocale } from "next-intl"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { appUrl } from "@/lib/urls"

export const dynamic = "force-static"
export const revalidate = false

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }))
}

export async function generateMetadata(props: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await props.params
  const t = await getTranslations({ locale, namespace: "web.privacy" })
  return { title: t("title"), description: t("intro") }
}

export default async function PrivacyPage(props: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await props.params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  const t = await getTranslations({ locale, namespace: "web.privacy" })

  const sections = [
    "collect",
    "purpose",
    "pseudonymity",
    "retention",
    "rights",
  ] as const

  return (
    <div className="container-wrapper flex flex-col gap-8 px-4 py-12 xl:px-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-muted-foreground max-w-[70ch] text-sm">
          {t("intro")}
        </p>
      </header>

      {sections.map((key) => (
        <section key={key} className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">{t(`${key}Heading`)}</h2>
          <p className="text-muted-foreground max-w-[70ch] text-sm">
            {t(`${key}Body`)}
          </p>
        </section>
      ))}

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-medium">{t("exerciseHeading")}</h2>
        <p className="text-muted-foreground max-w-[70ch] text-sm">
          {t("exerciseBody")}{" "}
          <a
            href={`${appUrl}/${locale}/settings`}
            className="underline underline-offset-4"
          >
            {t("exerciseLink")}
          </a>
          .
        </p>
      </section>
    </div>
  )
}
