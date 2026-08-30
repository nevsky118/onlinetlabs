import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import {
  InstructorView,
  studentsOverviewQuery,
} from "@/modules/instructor/server"
import { getBackendUserRole } from "@repo/auth/server"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@repo/design-system/components/page-header"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { forbidden, unauthorized } from "next/navigation"
import type { Metadata } from "next"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.instructorHome",
  })
  return { title: t("title"), description: t("description") }
}

export default async function InstructorPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("dashboard.app.instructorHome")

  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "instructor" && role !== "admin") forbidden()
  await prefetchQuery(studentsOverviewQuery())

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{t("title")}</PageHeaderHeading>
        <PageHeaderDescription>{t("description")}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper flex-1 section-soft pb-6">
        <div className="container">
          <HydrateClient>
            <InstructorView />
          </HydrateClient>
        </div>
      </div>
    </div>
  )
}
