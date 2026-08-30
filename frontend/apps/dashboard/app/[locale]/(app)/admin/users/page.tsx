import { fetchAdminUsers } from "@/modules/admin/actions"
import { searchParamsCache } from "@/modules/admin/lib/users-search-params"
import { UsersView } from "@/modules/admin/views/users-view"
import { getBackendUserRole, getSession } from "@repo/auth/server"
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
    namespace: "dashboard.app.adminUsers",
  })
  return { title: t("title"), description: t("description") }
}

export default async function AdminUsersPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>
  searchParams: Promise<Record<string, string | string[]>>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("dashboard.app.adminUsers")

  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  const sp = await searchParamsCache.parse(await searchParams)
  const session = await getSession()
  const currentUserId = session?.user?.id ?? null

  let data = null
  let error: string | null = null
  try {
    data = await fetchAdminUsers({
      page: sp.page,
      pageSize: sp.pageSize,
      sort: sp.sort,
      order: sp.order,
      search: sp.search,
      role: sp.role,
    })
  } catch (err) {
    error = err instanceof Error ? err.message : t("loadError")
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{t("title")}</PageHeaderHeading>
        <PageHeaderDescription>{t("description")}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper flex-1 section-soft pb-6">
        <div className="container">
          <UsersView data={data} error={error} currentUserId={currentUserId} />
        </div>
      </div>
    </div>
  )
}
