import { Link } from "@repo/i18n/navigation"
import { getTranslations } from "next-intl/server"

export default async function Forbidden() {
  const t = await getTranslations("dashboard.app.forbidden")
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">{t("heading")}</h1>
      <p className="text-muted-foreground">{t("description")}</p>
      <Link
        href="/"
        className="rounded-none bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
      >
        {t("home")}
      </Link>
    </div>
  )
}
