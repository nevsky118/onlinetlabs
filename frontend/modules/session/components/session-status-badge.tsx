"use client"

import type { SessionStatus } from "../types"
import { cn } from "@/lib/utils"
import { Badge } from "@/ui/badge"
import { Spinner } from "@/ui/spinner"

type Props = { status: SessionStatus }

const CONFIG: Record<
  SessionStatus,
  {
    label: string
    variant: "secondary" | "outline" | "destructive"
    dot?: string
    spinner?: boolean
  }
> = {
  active: { label: "Активна", variant: "secondary", dot: "bg-primary" },
  provisioning: { label: "Готовится", variant: "outline", spinner: true },
  ended: { label: "Завершена", variant: "outline" },
  error: { label: "Ошибка", variant: "destructive" },
}

export function SessionStatusBadge({ status }: Props) {
  const cfg = CONFIG[status]
  return (
    <Badge
      variant={cfg.variant}
      className="flex items-center gap-1.5 rounded-none"
    >
      {cfg.spinner ? (
        <Spinner className="size-2" />
      ) : cfg.dot ? (
        <span className={cn("size-2 rounded-full", cfg.dot)} />
      ) : null}
      {cfg.label}
    </Badge>
  )
}
