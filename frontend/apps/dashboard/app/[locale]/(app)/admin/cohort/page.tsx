import { getBackendUserRole } from "@repo/auth/server"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@repo/design-system/components/page-header"
import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { CohortView } from "@/modules/admin/views/cohort-view"
import { fetchCohortMetrics } from "@/modules/instructor/actions"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.adminCohort",
  })
  return { title: t("title"), description: t("description") }
}

export default async function AdminCohortPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("dashboard.app.adminCohort")

  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  let metrics = null
  let error: string | null = null
  try {
    metrics = await fetchCohortMetrics(true)
  } catch (err) {
    error = err instanceof Error ? err.message : t("loadError")
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{t("title")}</PageHeaderHeading>
        <PageHeaderDescription>{t("description")}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <CohortView metrics={metrics} error={error} />
        </div>
      </div>
    </div>
  )
}
