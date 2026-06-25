import type { Metadata } from "next"
import { forbidden, notFound, unauthorized } from "next/navigation"
import { getBackendUserRole } from "@/auth/role"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { fetchAdminData } from "@/modules/admin/actions"
import { AdminDataTable } from "@/modules/admin/components/admin-data-table"
import { searchParamsCache } from "@/modules/admin/lib/data-table-params"
import { getLogTable } from "@/modules/admin/lib/log-tables"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ table: string }>
}): Promise<Metadata> {
  const { table } = await params
  const meta = getLogTable(table)
  return { title: meta?.label ?? table }
}

export default async function AdminLogTablePage({
  params,
  searchParams,
}: {
  params: Promise<{ table: string }>
  searchParams: Promise<Record<string, string | string[]>>
}) {
  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  const { table } = await params
  const meta = getLogTable(table)
  if (!meta) notFound()

  const sp = await searchParamsCache.parse(await searchParams)

  let data = null
  let error: string | null = null
  try {
    data = await fetchAdminData(table, {
      page: sp.page,
      pageSize: sp.pageSize,
      sort: sp.sort,
      order: sp.order,
      search: sp.search,
    })
  } catch (err) {
    error = err instanceof Error ? err.message : "Ошибка загрузки"
  }

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{meta.label}</PageHeaderHeading>
        <PageHeaderDescription>Таблица: {table}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <AdminDataTable data={data} error={error} />
        </div>
      </div>
    </div>
  )
}
