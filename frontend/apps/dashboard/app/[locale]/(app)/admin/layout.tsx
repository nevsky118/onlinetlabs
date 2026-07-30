import { getBackendUserRole } from "@repo/auth/server"
import { forbidden, unauthorized } from "next/navigation"
import { setRequestLocale } from "next-intl/server"
import { AdminNavBar } from "./_components/admin-nav-bar"

export default async function AdminLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)

  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "admin") forbidden()

  return (
    <div className="flex flex-1 flex-col">
      <AdminNavBar />
      {children}
    </div>
  )
}
