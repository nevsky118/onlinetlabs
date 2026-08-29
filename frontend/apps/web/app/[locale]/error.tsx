"use client"

import { Button } from "@repo/design-system/ui/button"
import { useTranslations } from "next-intl"

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const t = useTranslations("web.error")

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 py-24">
      <h1 className="text-2xl font-bold">{t("heading")}</h1>
      <p className="text-muted-foreground">{t("description")}</p>
      <Button onClick={reset}>{t("retry")}</Button>
    </div>
  )
}
