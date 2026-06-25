import { forbidden, unauthorized } from "next/navigation"
import { AdminNavBar } from "./_components/admin-nav-bar"
import { getBackendUserRole } from "@/auth/role"

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
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
