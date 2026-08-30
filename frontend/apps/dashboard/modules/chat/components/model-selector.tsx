"use client"

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@repo/design-system/ui/select"
import { useTranslations } from "next-intl"

type Model = { id: string; label: string }

type Props = {
  models: Model[]
  canSelect: boolean
  value: string | undefined
  onValueChange: (value: string) => void
}

export function ModelSelector({
  models,
  canSelect,
  value,
  onValueChange,
}: Props) {
  const t = useTranslations("dashboard.chat.modelSelector")
  // With fewer than 2 models there is nothing to pick, so no dropdown (nothing to click).
  if (!canSelect || models.length < 2) return null

  return (
    <Select
      value={value}
      onValueChange={(nextValue) => {
        if (nextValue !== null) onValueChange(nextValue)
      }}
    >
      <SelectTrigger
        size="sm"
        className="max-w-[180px]"
        aria-label={t("ariaLabel")}
      >
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
