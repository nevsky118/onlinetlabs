"use client"

import { CheckIcon, ChevronDownIcon, CircleDashed, XIcon } from "lucide-react"
import { useState } from "react"
import type { ValidationRunListItem } from "../types"
import { useValidationRunDetail } from "../hooks/use-validation-run-detail"
import { formatDuration } from "../lib/validation-display"
import { ValidationStepRow } from "./validation-step-row"
import { cn } from "@/lib/utils"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/ui/collapsible"
import { Skeleton } from "@/ui/skeleton"

function timeAgo(dateStr: string): string {
  const diffMs = Date.now() - new Date(dateStr).getTime()
  const diffSec = Math.floor(diffMs / 1000)
  if (diffSec < 60) return `${diffSec} сек. назад`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin} мин. назад`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH} ч. назад`
  const diffD = Math.floor(diffH / 24)
  return `${diffD} д. назад`
}

type Props = {
  sessionId: string
  run: ValidationRunListItem
}

export function ValidationPastRunRow({ sessionId, run }: Props) {
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
            {timeAgo(run.startedAt)}
          </span>
          <span className="text-xs text-muted-foreground">
            {[
              run.passedChecks !== null && run.totalChecks !== null
                ? `${run.passedChecks}/${run.totalChecks} проверок`
                : null,
              run.durationMs !== null ? formatDuration(run.durationMs) : null,
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
