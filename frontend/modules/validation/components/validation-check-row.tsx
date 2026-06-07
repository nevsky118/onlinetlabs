"use client"

import {
  CheckIcon,
  ChevronDownIcon,
  CircleDashed,
  CopyIcon,
  Loader2,
  XIcon,
} from "lucide-react"
import { useState } from "react"
import type { ValidationCheck } from "../types"
import { commandFor } from "../lib/validation-display"
import { ValidationLogBlock } from "./validation-log-block"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/ui/collapsible"

function formatParams(params: Record<string, unknown>): string {
  return Object.entries(params)
    .map(([k, v]) => `${k}=${String(v)}`)
    .join(", ")
}

function formatKV(obj: Record<string, unknown>): string {
  return Object.entries(obj)
    .map(([k, v]) => `${k}=${String(v)}`)
    .join(", ")
}

type Props = {
  check: ValidationCheck
  isRunning?: boolean
  forceOpen?: boolean
}

export function ValidationCheckRow({
  check,
  isRunning = false,
  forceOpen,
}: Props) {
  const [open, setOpen] = useState(false)
  const effectiveOpen = forceOpen ?? open

  const isDone = !isRunning
  const hasDetails = check.log || isDone

  const icon = !isDone ? (
    <Loader2 className="size-3 animate-spin text-muted-foreground" />
  ) : check.ok ? (
    <CheckIcon className="size-3 text-foreground" />
  ) : (
    <XIcon className="size-3 text-destructive" />
  )

  const label = `${check.kind}(${formatParams(check.params)})`

  const cmd = commandFor(check)

  function handleCopy(e: React.MouseEvent) {
    e.stopPropagation()
    void navigator.clipboard.writeText(cmd)
  }

  if (!hasDetails) {
    return (
      <div className="flex items-center gap-2 px-4 py-1.5">
        {icon}
        <span className="flex-1 text-xs text-muted-foreground">{label}</span>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={handleCopy}
          aria-label="Копировать команду"
        >
          <CopyIcon />
        </Button>
      </div>
    )
  }

  return (
    <Collapsible
      open={effectiveOpen}
      onOpenChange={forceOpen !== undefined ? undefined : setOpen}
    >
      <CollapsibleTrigger className="flex w-full items-center gap-2 px-4 py-1.5 hover:bg-muted/50">
        {icon}
        <span
          className={cn(
            "flex-1 text-left text-xs text-muted-foreground",
            !check.ok && isDone && "text-destructive"
          )}
        >
          {label}
        </span>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={handleCopy}
          aria-label="Копировать команду"
        >
          <CopyIcon />
        </Button>
        <ChevronDownIcon
          className={cn(
            "size-3 text-muted-foreground transition-transform",
            open && "rotate-180"
          )}
        />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="flex flex-col gap-1 px-4 pb-2">
          {check.actual && (check.actual as Record<string, unknown>).error ? (
            <p className="text-xs text-destructive">
              Ошибка: {String((check.actual as Record<string, unknown>).error)}
            </p>
          ) : isDone ? (
            <>
              <p className="text-xs text-muted-foreground">
                <span className="text-foreground">ожидалось:</span>{" "}
                {formatKV(check.expected)}
              </p>
              <p className="text-xs text-muted-foreground">
                <span className="text-foreground">фактически:</span>{" "}
                {formatKV(check.actual)}
              </p>
            </>
          ) : null}
          {check.log && <ValidationLogBlock text={check.log} />}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
