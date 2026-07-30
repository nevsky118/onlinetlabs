import { getSession } from "@repo/auth/server"
import { Button } from "@repo/design-system/ui/button"
import { redirect } from "@repo/i18n/navigation"
import { RocketIcon } from "lucide-react"
import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { LaunchLabConfirmTrigger } from "@/modules/session"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.launchLab",
  })
  return { title: t("metaTitle") }
}

/**
 * Next.js cannot nest a static segment under a catch-all ("launch" under [...slug]).
 * This single /labs/[...slug] route parses the path tail itself.
 */
export default async function LaunchLabPage(props: {
  params: Promise<{ locale: string; slug: string[] }>
}) {
  const { locale, slug } = await props.params
  setRequestLocale(locale)
  const t = await getTranslations("dashboard.app.launchLab")
  if (slug.at(-1) !== "launch") {
    notFound()
  }

  const labSlug = slug.slice(0, -1).join("/")
  if (!labSlug) {
    notFound()
  }

  const session = await getSession()
  if (!session?.user) {
    redirect({
      href: `/sign-in?redirect=${encodeURIComponent(`/${locale}/labs/${labSlug}/launch`)}`,
      locale,
    })
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
      <div className="flex flex-col gap-1">
        <h1 className="text-lg font-semibold tracking-tight">{t("heading")}</h1>
        <p className="text-muted-foreground text-sm">{labSlug}</p>
      </div>
      <LaunchLabConfirmTrigger labSlug={labSlug}>
        <Button>
          <RocketIcon data-icon="inline-start" />
          {t("launchButton")}
        </Button>
      </LaunchLabConfirmTrigger>
    </div>
  )
}
