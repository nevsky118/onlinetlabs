import { adminMessages } from "@/lib/messages"
import { getBackendUserRole } from "@repo/auth/server"
import { NextIntlClientProvider } from "next-intl"
import { setRequestLocale } from "next-intl/server"
import { forbidden, unauthorized } from "next/navigation"
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
    <NextIntlClientProvider messages={await adminMessages(locale)}>
      <div className="flex flex-1 flex-col">
        <AdminNavBar />
        {children}
      </div>
    </NextIntlClientProvider>
  )
}
