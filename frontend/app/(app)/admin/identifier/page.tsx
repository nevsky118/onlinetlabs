import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getBackendUserRole } from "@/auth/role"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { fetchIdentifierEval } from "@/modules/admin/actions"
import { IdentifierView } from "@/modules/admin/views/identifier-view"

const title = "Идентификатор режима"
const description =
  "Operating-кривая, матрица путаницы и first-match диагностика идентификатора"

export const metadata: Metadata = { title, description }

export default async function IdentifierPage() {
  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  let data = null
  let error: string | null = null
  try {
    data = await fetchIdentifierEval()
  } catch (e) {
    error = e instanceof Error ? e.message : "Ошибка загрузки"
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <IdentifierView data={data} error={error} />
        </div>
      </div>
    </div>
  )
}
