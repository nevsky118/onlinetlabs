import { forbidden, unauthorized } from "next/navigation"
import { AdminTabs } from "./_components/admin-tabs"
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
      <div className="container-wrapper">
        <div className="container pt-4">
          <AdminTabs />
        </div>
      </div>
      {children}
    </div>
  )
}
