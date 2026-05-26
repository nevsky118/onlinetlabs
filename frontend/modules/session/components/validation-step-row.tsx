"use client"

import {
  CheckIcon,
  ChevronDownIcon,
  CircleDashed,
  Loader2,
  XIcon,
} from "lucide-react"
import { useState } from "react"
import type { ValidationStep } from "../hooks/use-validation-run-detail"
import { ValidationCheckRow } from "./validation-check-row"
import { cn } from "@/lib/utils"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/ui/collapsible"

type Props = {
  step: ValidationStep
  isActive?: boolean
  forceOpen?: boolean
}

export function ValidationStepRow({
  step,
  isActive = false,
  forceOpen,
}: Props) {
  const [open, setOpen] = useState(false)
  const effectiveOpen = forceOpen ?? open

  const passedCount = step.checks.filter((c) => c.ok).length
  const total = step.checks.length
  const firstFailedCheckIdx =
    forceOpen !== undefined ? step.checks.findIndex((c) => !c.ok) : -1

  const isDone = !isActive
  const stepFinished = isDone && step.checks.length > 0
  const icon = isActive ? (
    <Loader2 className="size-3.5 animate-spin text-muted-foreground" />
  ) : !stepFinished ? (
    <CircleDashed className="size-3.5 text-muted-foreground" />
  ) : step.ok ? (
    <CheckIcon className="size-3.5 text-foreground" />
  ) : (
    <XIcon className="size-3.5 text-destructive" />
  )

  return (
    <Collapsible
      open={effectiveOpen}
      onOpenChange={forceOpen !== undefined ? undefined : setOpen}
    >
      <CollapsibleTrigger className="flex w-full items-center gap-2 px-4 py-2 hover:bg-muted/50">
        {icon}

        <span
          className={cn(
            "flex-1 text-left text-xs font-medium",
            !step.ok && isDone && "text-destructive"
          )}
        >
          {step.title}
        </span>
        {total > 0 && (
          <span className="text-xs text-muted-foreground">
            {passedCount}/{total}
          </span>
        )}
        <ChevronDownIcon
          className={cn(
            "size-3 text-muted-foreground transition-transform",
            open && "rotate-180"
          )}
        />
      </CollapsibleTrigger>
      {isActive && <div className="h-0.5 bg-primary animate-pulse" />}
      <CollapsibleContent>
        <div className="flex flex-col border-l border-border ml-6">
          {step.checks.map((check, i) => (
            <ValidationCheckRow
              key={i}
              check={check}
              isRunning={isActive && i === step.checks.length - 1}
              forceOpen={i === firstFailedCheckIdx ? true : undefined}
            />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
