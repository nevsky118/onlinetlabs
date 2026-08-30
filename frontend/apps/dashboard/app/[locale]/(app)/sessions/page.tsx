import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import { SessionsView, sessionsListQuery } from "@/modules/session/server"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@repo/design-system/components/page-header"
import { getTranslations, setRequestLocale } from "next-intl/server"
import type { Metadata } from "next"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.sessions",
  })
  return { title: t("title"), description: t("description") }
}

export default async function SessionsPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("dashboard.app.sessions")

  await prefetchQuery(sessionsListQuery())

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{t("title")}</PageHeaderHeading>
        <PageHeaderDescription>{t("description")}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper flex-1 section-soft pb-6">
        <div className="container">
          <HydrateClient>
            <SessionsView />
          </HydrateClient>
        </div>
      </div>
    </div>
  )
}
