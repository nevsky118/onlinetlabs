"use client"

import { cn } from "@repo/design-system/lib/utils"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@repo/design-system/ui/collapsible"
import {
  CheckIcon,
  ChevronDownIcon,
  CircleDashed,
  Loader2,
  XIcon,
} from "lucide-react"
import { useState } from "react"
import type { ValidationStep } from "../types"
import { ValidationCheckRow } from "./validation-check-row"

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

  const passedCount = step.checks.filter((check) => check.ok).length
  const total = step.checks.length
  const firstFailedCheckIdx =
    forceOpen !== undefined ? step.checks.findIndex((check) => !check.ok) : -1

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
      {isActive && <div className="h-0.5 animate-pulse bg-primary" />}
      <CollapsibleContent>
        <div className="ml-6 flex flex-col border-l border-border">
          {step.checks.map((check, index) => (
            <ValidationCheckRow
              key={index}
              check={check}
              isRunning={isActive && index === step.checks.length - 1}
              forceOpen={index === firstFailedCheckIdx ? true : undefined}
            />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
