import { fetchArmAnalysis } from "@/modules/admin/actions"
import { AbView } from "@/modules/admin/views/ab-view"
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
  let errorMessage: string | null = null
  try {
    data = await fetchArmAnalysis()
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : t("unknownError")
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{t("title")}</PageHeaderHeading>
        <PageHeaderDescription>{t("description")}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper flex-1 section-soft pb-6">
        <div className="container">
          <AbView data={data} error={errorMessage} />
        </div>
      </div>
    </div>
  )
}
