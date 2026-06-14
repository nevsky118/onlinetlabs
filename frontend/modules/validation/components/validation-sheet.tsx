"use client"

import { Loader2, PlayIcon } from "lucide-react"
import { useEffect, useState } from "react"
import { useValidationRuns } from "../hooks/use-validation-runs"
import { useValidationStream } from "../hooks/use-validation-stream"
import { ValidationPastRunRow } from "./validation-past-run-row"
import { ValidationStepRow } from "./validation-step-row"
import { LabProgressBadge, useLabProgress } from "@/modules/progress"
import { Button } from "@/ui/button"
import { Separator } from "@/ui/separator"
import {
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/ui/sheet"
import { Skeleton } from "@/ui/skeleton"

type Props = {
  sessionId: string
  labSlug: string
}

export function ValidationSheet({ sessionId, labSlug }: Props) {
  const { runs, isLoading, mutate } = useValidationRuns(sessionId)
  const { state, start } = useValidationStream(sessionId)
  const { progress, refresh: refreshProgress } = useLabProgress(labSlug)
  const [expandedStepId, setExpandedStepId] = useState<string | null>(null)

  useEffect(() => {
    if (state.status === "passed" || state.status === "failed") {
      void mutate()
      void refreshProgress()
      if (state.status === "failed") {
        const firstFailed = state.steps.find((s) => !s.ok)
        setExpandedStepId(firstFailed?.id ?? null)
      } else {
        setExpandedStepId(null)
      }
    }
    if (state.status === "running") {
      setExpandedStepId(null)
    }
  }, [state.status, mutate, refreshProgress, state.steps])

  const isRunning = state.status === "running"
  const hasActiveRun =
    state.status === "running" ||
    state.status === "passed" ||
    state.status === "failed" ||
    state.status === "error"

  return (
    <SheetContent side="right" className="flex w-full flex-col sm:max-w-md">
      <SheetHeader>
        <SheetTitle>Проверка лабы</SheetTitle>
        <SheetDescription>
          Запускает проверки в живой среде GNS3
        </SheetDescription>
        {progress ? (
          <LabProgressBadge progress={progress} className="mt-1" />
        ) : null}
      </SheetHeader>

      <div className="flex flex-1 flex-col overflow-y-auto">
        {hasActiveRun && state.steps.length > 0 && (
          <>
            <div className="px-4 py-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Текущий прогон
              </p>
            </div>
            <div className="flex flex-col">
              {state.steps.map((step, i) => (
                <ValidationStepRow
                  key={step.id}
                  step={step}
                  isActive={isRunning && i === state.steps.length - 1}
                  forceOpen={expandedStepId === step.id ? true : undefined}
                />
              ))}
            </div>
            <Separator />
          </>
        )}

        <div className="px-4 py-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            История
          </p>
        </div>

        {isLoading ? (
          <div className="flex flex-col gap-2 px-4 py-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : runs.length === 0 ? (
          <p className="px-4 py-2 text-xs text-muted-foreground">
            Прогонов пока нет
          </p>
        ) : (
          <div className="flex flex-col">
            {runs.map((run) => (
              <ValidationPastRunRow
                key={run.id}
                sessionId={sessionId}
                run={run}
              />
            ))}
          </div>
        )}
      </div>

      <SheetFooter>
        <Button
          onClick={() => start(labSlug)}
          disabled={isRunning}
          className="w-full rounded-none"
        >
          {isRunning ? (
            <>
              <Loader2 data-icon="inline-start" className="animate-spin" />
              Идёт проверка...
            </>
          ) : (
            <>
              <PlayIcon data-icon="inline-start" />
              Запустить заново
            </>
          )}
        </Button>
      </SheetFooter>
    </SheetContent>
  )
}
