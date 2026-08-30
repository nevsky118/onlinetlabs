import { ContentCard } from "@/app-components/content-card"
import { absoluteUrl } from "@/lib/absolute-url"
import { labs } from "@/lib/source"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@repo/design-system/components/page-header"
import { routing } from "@repo/i18n/routing"
import { getTranslations, setRequestLocale } from "next-intl/server"
import type { Metadata } from "next"

export const dynamic = "force-static"
export const revalidate = false

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("web.labs")

  return {
    title: t("title"),
    description: t("description"),
    alternates: {
      canonical: absoluteUrl(`/${locale}/labs`),
      languages: Object.fromEntries(
        routing.locales.map((alternate) => [
          alternate,
          absoluteUrl(`/${alternate}/labs`),
        ])
      ),
    },
  }
}

export default async function LabsPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("web.labs")

  // Show only top-level lab pages, not nested ones like guides.
  const pages = labs.getPages(locale).filter((page) => page.slugs.length === 1)

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{t("title")}</PageHeaderHeading>
        <PageHeaderDescription>{t("description")}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper flex-1 section-soft pb-6">
        <div className="container">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {pages.map((page) => (
              <ContentCard
                key={page.url}
                href={page.url}
                title={page.data.title}
                tasks={page.data.tasks}
                difficulty={page.data.difficulty}
                tags={page.data.tags}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
