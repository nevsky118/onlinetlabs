"use client"

import { cn } from "@repo/design-system/lib/utils"
import { Badge } from "@repo/design-system/ui/badge"
import { Spinner } from "@repo/design-system/ui/spinner"
import { useTranslations } from "next-intl"
import type { SessionStatus } from "../types"

type Props = { status: SessionStatus }

const CONFIG: Record<
  SessionStatus,
  {
    variant: "secondary" | "outline" | "destructive"
    dot?: string
    spinner?: boolean
  }
> = {
  active: { variant: "secondary", dot: "bg-primary" },
  provisioning: { variant: "outline", spinner: true },
  ended: { variant: "outline" },
  error: { variant: "destructive" },
}

export function SessionStatusBadge({ status }: Props) {
  const t = useTranslations("dashboard.session.statusBadge")
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
      {t(status)}
    </Badge>
  )
}
