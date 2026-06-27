import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { getBackendUserRole } from "@/auth/role"
import { getSession } from "@/auth/session"
import { SettingsView } from "@/modules/settings/views/settings-view"

export const metadata: Metadata = { title: "Настройки" }

export default async function SettingsPage() {
  const session = await getSession()
  if (!session?.user) redirect("/sign-in?redirect=/settings")

  const role = await getBackendUserRole()

  return (
    <div className="flex flex-1 flex-col">
      <div className="border-grid border-b">
        <div className="mx-auto max-w-3xl px-4 py-6">
          <h1 className="text-2xl font-semibold tracking-tight">Настройки</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Аккаунт, тема, данные и безопасность
          </p>
        </div>
      </div>
      <SettingsView
        account={{
          name: session.user.name ?? null,
          email: session.user.email ?? null,
          image: session.user.image ?? null,
          role,
        }}
      />
    </div>
  )
}
