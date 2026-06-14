import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getBackendUserRole } from "@/auth/role"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import {
  InstructorView,
  studentsOverviewQuery,
} from "@/modules/instructor/server"

const title = "Кабинет преподавателя"
const description = "Прогресс учеников, подсказки и активность"

export const metadata: Metadata = { title, description }

export default async function InstructorPage() {
  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "instructor" && role !== "admin") forbidden()
  await prefetchQuery(studentsOverviewQuery())

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <HydrateClient>
            <InstructorView />
          </HydrateClient>
        </div>
      </div>
    </div>
  )
}
