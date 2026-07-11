"use client"

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/ui/select"

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
  // <2 моделей — выбирать нечего, не показываем дропдаун (нечего тыкать).
  if (!canSelect || models.length < 2) return null

  return (
    <Select
      value={value}
      onValueChange={(v) => {
        if (v !== null) onValueChange(v)
      }}
    >
      <SelectTrigger
        size="sm"
        className="max-w-[180px]"
        aria-label="Выбор модели"
      >
        <SelectValue placeholder="Модель" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          {models.map((m) => (
            <SelectItem key={m.id} value={m.id}>
              {m.label}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  )
}
