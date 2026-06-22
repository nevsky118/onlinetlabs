import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getBackendUserRole } from "@/auth/role"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { fetchArmAnalysis } from "@/modules/admin/actions"
import { AbView } from "@/modules/admin/views/ab-view"

const title = "A/B-эффект"
const description =
  "Сравнение плеч эксперимента: каузальный анализ рандомизированных групп"

export const metadata: Metadata = { title, description }

export default async function AbPage() {
  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  let data = null
  let error: string | null = null
  try {
    data = await fetchArmAnalysis()
  } catch (e) {
    error = e instanceof Error ? e.message : "Неизвестная ошибка"
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <AbView data={data} error={error} />
        </div>
      </div>
    </div>
  )
}
