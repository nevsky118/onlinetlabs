import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getBackendUserRole } from "@/auth/role"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { CohortView } from "@/modules/admin/views/cohort-view"
import { fetchCohortMetrics } from "@/modules/instructor/actions"

const title = "Когорта"
const description = "KM/reach + автономия на L2-холдауте по навыкам"

export const metadata: Metadata = { title, description }

export default async function AdminCohortPage() {
  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  let metrics = null
  let error: string | null = null
  try {
    metrics = await fetchCohortMetrics(true)
  } catch (err) {
    error = err instanceof Error ? err.message : "Ошибка загрузки метрик"
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <CohortView metrics={metrics} error={error} />
        </div>
      </div>
    </div>
  )
}
