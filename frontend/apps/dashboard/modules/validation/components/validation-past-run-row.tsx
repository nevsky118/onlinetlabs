"use client"

import { formatRelativeTime } from "@/lib/format-duration"
import { cn } from "@repo/design-system/lib/utils"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@repo/design-system/ui/collapsible"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { CheckIcon, ChevronDownIcon, CircleDashed, XIcon } from "lucide-react"
import { useFormatter, useTranslations } from "next-intl"
import { useState } from "react"
import type { ValidationRunListItem } from "../types"
import { useValidationRunDetail } from "../hooks/use-validation-run-detail"
import { formatDuration } from "../lib/validation-display"
import { ValidationStepRow } from "./validation-step-row"

type Props = {
  sessionId: string
  run: ValidationRunListItem
}

export function ValidationPastRunRow({ sessionId, run }: Props) {
  const t = useTranslations("dashboard.validation.pastRunRow")
  const durationT = useTranslations("dashboard.validation.duration")
  const format = useFormatter()
  const [open, setOpen] = useState(false)
  const { detail, isLoading } = useValidationRunDetail(
    sessionId,
    open ? run.id : null
  )

  const icon =
    run.status === "passed" ? (
      <CheckIcon className="size-3.5 shrink-0 text-foreground" />
    ) : run.status === "failed" || run.status === "error" ? (
      <XIcon className="size-3.5 shrink-0 text-destructive" />
    ) : (
      <CircleDashed className="size-3.5 shrink-0 text-muted-foreground" />
    )

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex w-full items-center gap-2 px-4 py-2.5 hover:bg-muted/50">
        {icon}
        <div className="flex flex-1 flex-col items-start gap-0.5">
          <span className="text-xs text-muted-foreground">
            {formatRelativeTime(run.startedAt, format)}
          </span>
          <span className="text-xs text-muted-foreground">
            {[
              run.passedChecks !== null && run.totalChecks !== null
                ? t("checksRatio", {
                    passed: run.passedChecks,
                    total: run.totalChecks,
                  })
                : null,
              run.durationMs !== null
                ? formatDuration(run.durationMs, durationT)
                : null,
            ]
              .filter(Boolean)
              .join(" · ")}
          </span>
        </div>
        <ChevronDownIcon
          className={cn(
            "size-3 text-muted-foreground transition-transform",
            open && "rotate-180"
          )}
        />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="flex flex-col">
          {isLoading ? (
            <div className="flex flex-col gap-2 px-4 py-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          ) : detail ? (
            detail.steps.map((step) => (
              <ValidationStepRow key={step.id} step={step} isActive={false} />
            ))
          ) : null}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
