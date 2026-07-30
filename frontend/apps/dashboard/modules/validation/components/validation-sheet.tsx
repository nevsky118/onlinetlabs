"use client"

import { Button } from "@repo/design-system/ui/button"
import { Separator } from "@repo/design-system/ui/separator"
import {
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@repo/design-system/ui/sheet"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { Loader2, PlayIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { useValidationRuns } from "../hooks/use-validation-runs"
import { useValidationStream } from "../hooks/use-validation-stream"
import { ValidationPastRunRow } from "./validation-past-run-row"
import { ValidationStepRow } from "./validation-step-row"
import { LabProgressBadge, useLabProgress } from "@/modules/progress"

type Props = {
  sessionId: string
  labSlug: string
}

export function ValidationSheet({ sessionId, labSlug }: Props) {
  const t = useTranslations("dashboard.validation.sheet")
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
        <SheetTitle>{t("title")}</SheetTitle>
        <SheetDescription>{t("description")}</SheetDescription>
        {progress ? (
          <LabProgressBadge progress={progress} className="mt-1" />
        ) : null}
      </SheetHeader>

      <div className="flex flex-1 flex-col overflow-y-auto">
        {hasActiveRun && state.steps.length > 0 && (
          <>
            <div className="px-4 py-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                {t("currentRun")}
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
            {t("history")}
          </p>
        </div>

        {isLoading ? (
          <div className="flex flex-col gap-2 px-4 py-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : runs.length === 0 ? (
          <p className="px-4 py-2 text-xs text-muted-foreground">
            {t("noRuns")}
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
              {t("running")}
            </>
          ) : (
            <>
              <PlayIcon data-icon="inline-start" />
              {t("runAgain")}
            </>
          )}
        </Button>
      </SheetFooter>
    </SheetContent>
  )
}
