import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@repo/design-system/components/page-header"
import { routing } from "@repo/i18n/routing"
import type { Metadata } from "next"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { ContentCard } from "@/app-components/content-card"
import { absoluteUrl } from "@/lib/absolute-url"
import { course } from "@/lib/source"

export const dynamic = "force-static"
export const revalidate = false

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("web.courses")

  return {
    title: t("title"),
    description: t("description"),
    alternates: {
      canonical: absoluteUrl(`/${locale}/courses`),
      languages: Object.fromEntries(
        routing.locales.map((l) => [l, absoluteUrl(`/${l}/courses`)])
      ),
    },
  }
}

export default async function CoursesPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("web.courses")

  const pages = course.getPages(locale)

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{t("title")}</PageHeaderHeading>
        <PageHeaderDescription>{t("description")}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {pages.map((page) => (
              <ContentCard
                key={page.url}
                href={page.url}
                title={page.data.title}
                description={page.data.description}
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
