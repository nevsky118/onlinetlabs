import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getBackendUserRole } from "@/auth/role"
import { getSession } from "@/auth/session"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { fetchAdminUsers } from "@/modules/admin/actions"
import { searchParamsCache } from "@/modules/admin/lib/users-search-params"
import { UsersView } from "@/modules/admin/views/users-view"

const title = "Пользователи"
const description = "Управление ролями и правами"

export const metadata: Metadata = { title, description }

export default async function AdminUsersPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[]>>
}) {
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
          <UsersView data={data} error={error} currentUserId={currentUserId} />
        </div>
      </div>
    </div>
  )
}
