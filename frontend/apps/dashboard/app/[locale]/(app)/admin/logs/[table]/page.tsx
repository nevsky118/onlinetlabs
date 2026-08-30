import { fetchAdminData } from "@/modules/admin/actions"
import { AdminDataTable } from "@/modules/admin/components/admin-data-table"
import { searchParamsCache } from "@/modules/admin/lib/data-table-params"
import { getLogTable, getLogTableLabel } from "@/modules/admin/lib/log-tables"
import { getBackendUserRole } from "@repo/auth/server"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { forbidden, notFound, unauthorized } from "next/navigation"
import type { Metadata } from "next"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; table: string }>
}): Promise<Metadata> {
  const { locale, table } = await params
  const meta = getLogTable(table)
  if (!meta) return { title: table }
  const t = await getTranslations({
    locale,
    namespace: "dashboard.admin.logTables",
  })
  return { title: getLogTableLabel(t, meta.slug) }
}

export default async function AdminLogTablePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; table: string }>
  searchParams: Promise<Record<string, string | string[]>>
}) {
  const { locale, table } = await params
  setRequestLocale(locale)

  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  const meta = getLogTable(table)
  if (!meta) notFound()

  const logTableT = await getTranslations({
    locale,
    namespace: "dashboard.admin.logTables",
  })
  const label = getLogTableLabel(logTableT, meta.slug)
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.adminLogTable",
  })

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
    error = err instanceof Error ? err.message : t("loadError")
  }

  return (
    <div className="flex h-[calc(100svh-var(--header-height)-var(--footer-height)-3rem)] flex-col">
      {/* Compact header — keeps the data table in the viewport instead of a full-page hero */}
      <div className="shrink-0 border-b border-grid">
        <div className="container-wrapper">
          <div className="container flex flex-wrap items-baseline gap-x-3 gap-y-1 py-4">
            <h1 className="text-xl font-semibold tracking-tight">{label}</h1>
            <span className="font-mono text-xs text-muted-foreground">
              {table}
            </span>
          </div>
        </div>
      </div>
      <div className="container-wrapper flex min-h-0 flex-1 flex-col">
        <div className="container flex min-h-0 flex-1 flex-col py-4">
          <AdminDataTable data={data} error={error} />
        </div>
      </div>
    </div>
  )
}
