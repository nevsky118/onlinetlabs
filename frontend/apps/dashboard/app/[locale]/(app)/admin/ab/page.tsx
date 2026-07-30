import { getBackendUserRole } from "@repo/auth/server"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@repo/design-system/components/page-header"
import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { fetchArmAnalysis } from "@/modules/admin/actions"
import { AbView } from "@/modules/admin/views/ab-view"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.adminAb",
  })
  return { title: t("title"), description: t("description") }
}

export default async function AbPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("dashboard.app.adminAb")

  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  let data = null
  let error: string | null = null
  try {
    data = await fetchArmAnalysis()
  } catch (e) {
    error = e instanceof Error ? e.message : t("unknownError")
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{t("title")}</PageHeaderHeading>
        <PageHeaderDescription>{t("description")}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <AbView data={data} error={error} />
        </div>
      </div>
    </div>
  )
}
