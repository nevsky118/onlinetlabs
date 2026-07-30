import { Link } from "@repo/i18n/navigation"
import { getTranslations } from "next-intl/server"

export default async function Unauthorized() {
  const t = await getTranslations("dashboard.app.unauthorized")
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">{t("heading")}</h1>
      <p className="text-muted-foreground">{t("description")}</p>
      <Link
        href="/sign-in"
        className="bg-primary text-primary-foreground rounded-none px-4 py-2 text-sm font-medium"
      >
        {t("signIn")}
      </Link>
    </div>
  )
}
