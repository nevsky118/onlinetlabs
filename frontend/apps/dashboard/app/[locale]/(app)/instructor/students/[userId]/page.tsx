import { getBackendUserRole } from "@repo/auth/server"
import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import {
  StudentDetailView,
  studentDetailQuery,
} from "@/modules/instructor/server"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.studentDetail",
  })
  return { title: t("title"), description: t("description") }
}

export default async function StudentDetailPage({
  params,
}: {
  params: Promise<{ locale: string; userId: string }>
}) {
  const { locale, userId } = await params
  setRequestLocale(locale)

  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "instructor" && role !== "admin") forbidden()
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
