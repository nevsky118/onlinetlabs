import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getBackendUserRole } from "@/auth/role"
import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import {
  StudentDetailView,
  studentDetailQuery,
} from "@/modules/instructor/server"

export const metadata: Metadata = {
  title: "Прогресс ученика",
  description: "Детальный прогресс ученика по лабам",
}

export default async function StudentDetailPage({
  params,
}: {
  params: Promise<{ userId: string }>
}) {
  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "instructor" && role !== "admin") forbidden()
  const { userId } = await params
  await prefetchQuery(studentDetailQuery(userId))

  return (
    <div className="container-wrapper section-soft flex flex-1 flex-col pb-6">
      <div className="container py-8">
        <HydrateClient>
          <StudentDetailView userId={userId} />
        </HydrateClient>
      </div>
    </div>
  )
}
