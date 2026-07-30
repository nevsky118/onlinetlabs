import { getBackendUserRole, getSession } from "@repo/auth/server"
import { redirect } from "@repo/i18n/navigation"
import type { Metadata } from "next"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { SettingsView } from "@/modules/settings/views/settings-view"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.settingsPage",
  })
  return { title: t("metaTitle") }
}

export default async function SettingsPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("dashboard.app.settingsPage")

  const session = await getSession()
  if (!session?.user) {
    // Explicit return, the re-exported redirect is not typed as never so TS will not narrow session
    return redirect({ href: `/sign-in?redirect=/${locale}/settings`, locale })
  }

  const role = await getBackendUserRole()

  return (
    <div className="flex flex-1 flex-col">
      <div className="border-grid border-b">
        <div className="mx-auto max-w-3xl px-4 py-6">
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("heading")}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("description")}
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
