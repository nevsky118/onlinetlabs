"use client"

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@repo/design-system/ui/select"
import { Spinner } from "@repo/design-system/ui/spinner"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { useDefaultModel } from "../hooks/use-default-model"

export function ModelControl() {
  const t = useTranslations("dashboard.settings.model")
  const { models, selectedModelId, save, isSaving } = useDefaultModel(() =>
    toast.error(t("toastFailed"))
  )

  if (models === null) {
    return <Spinner className="size-4" labelLoading={t("loading")} />
  }
  if (models.length === 0) {
    return (
      <span className="text-sm text-muted-foreground">{t("unavailable")}</span>
    )
  }

  return (
    <Select
      value={selectedModelId ?? undefined}
      disabled={isSaving}
      onValueChange={(value) => {
        if (value === null) return
        save(value, { onSuccess: () => toast.success(t("toastSaved")) })
      }}
    >
      <SelectTrigger className="w-56">
        <SelectValue placeholder={t("placeholder")} />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          {models.map((model) => (
            <SelectItem key={model.id} value={model.id}>
              {model.label}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  )
}
