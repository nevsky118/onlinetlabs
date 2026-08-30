"use client"

import { LabProgressBadge, useLabProgress } from "@/modules/progress"
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

  // Which step is open follows the run status, so it is adjusted during render.
  const [lastStatus, setLastStatus] = useState(state.status)
  if (state.status !== lastStatus) {
    setLastStatus(state.status)
    switch (state.status) {
      case "failed":
        setExpandedStepId(state.steps.find((step) => !step.ok)?.id ?? null)
        break
      case "passed":
      case "running":
        setExpandedStepId(null)
        break
      default:
        break
    }
  }

  useEffect(() => {
    if (state.status === "passed" || state.status === "failed") {
      void mutate()
      void refreshProgress()
    }
  }, [state.status, mutate, refreshProgress])

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
              <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                {t("currentRun")}
              </p>
            </div>
            <div className="flex flex-col">
              {state.steps.map((step, index) => (
                <ValidationStepRow
                  key={step.id}
                  step={step}
                  isActive={isRunning && index === state.steps.length - 1}
                  forceOpen={expandedStepId === step.id ? true : undefined}
                />
              ))}
            </div>
            <Separator />
          </>
        )}

        <div className="px-4 py-2">
          <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
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
