"use client"

import { webUrl } from "@/lib/config"
import { useLocale, useTranslations } from "next-intl"

/** The policy and terms live on the public site, a different origin from the dashboard. */
export function DocumentsControl() {
  const t = useTranslations("dashboard.settings.documents")
  const locale = useLocale()

  return (
    <div className="flex items-center gap-4 text-sm">
      <a
        href={`${webUrl}/${locale}/privacy`}
        target="_blank"
        rel="noreferrer"
        className="underline underline-offset-4"
      >
        {t("privacy")}
      </a>
      <a
        href={`${webUrl}/${locale}/terms`}
        target="_blank"
        rel="noreferrer"
        className="underline underline-offset-4"
      >
        {t("terms")}
      </a>
    </div>
  )
}
