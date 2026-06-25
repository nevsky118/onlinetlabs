import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getBackendUserRole } from "@/auth/role"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { fetchAdminLabs } from "@/modules/admin/actions"
import { LabsView } from "@/modules/admin/views/labs-view"

const title = "Лабы"
const description = "Управление лабами и GNS3-шаблонами"

export const metadata: Metadata = { title, description }

export default async function AdminLabsPage() {
  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  let data = null
  let error: string | null = null
  try {
    data = await fetchAdminLabs()
  } catch (err) {
    error = err instanceof Error ? err.message : "Ошибка загрузки"
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <LabsView data={data} error={error} />
        </div>
      </div>
    </div>
  )
}
