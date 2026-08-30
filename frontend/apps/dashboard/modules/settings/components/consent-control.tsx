"use client"

import { useStudyConsent } from "@/modules/consent"
import { Spinner } from "@repo/design-system/ui/spinner"
import { Switch } from "@repo/design-system/ui/switch"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

export function ConsentControl() {
  const t = useTranslations("dashboard.settings.consent")
  const { granted, toggle, isSaving } = useStudyConsent()

  if (granted === null) {
    return <Spinner className="size-4" labelLoading={t("loading")} />
  }

  async function handleChange(next: boolean) {
    try {
      await toggle(next)
      toast.success(next ? t("toastEnabled") : t("toastRevoked"))
    } catch {
      toast.error(t("toastFailed"))
    }
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-muted-foreground tabular-nums">
        {granted ? t("enabled") : t("disabled")}
      </span>
      <Switch
        checked={granted}
        disabled={isSaving}
        onCheckedChange={handleChange}
        aria-label={t("ariaLabel")}
      />
    </div>
  )
}
