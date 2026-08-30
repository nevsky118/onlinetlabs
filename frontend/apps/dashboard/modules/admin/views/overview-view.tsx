"use client"

import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@repo/design-system/ui/alert"
import { Button } from "@repo/design-system/ui/button"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { useTranslations } from "next-intl"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import type { Overview } from "../types"
import { fetchOverview } from "../actions"
import { KpiCard } from "../components/kpi-card"

function fmtPct(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

function fmtNum(value: number, digits = 1): string {
  return value.toFixed(digits)
}

// Grid of KPI cards for the "Overview" section
export function OverviewView() {
  const t = useTranslations("dashboard.admin.overview")
  const router = useRouter()
  const [data, setData] = useState<Overview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOverview()
      .then(setData)
      .catch((reason: unknown) =>
        setError(reason instanceof Error ? reason.message : t("errorFallback"))
      )
      .finally(() => setLoading(false))
  }, [t])

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 8 }).map((_, index) => (
          <Skeleton key={index} className="h-24" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Alert>
        <AlertTitle>{t("errorTitle")}</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!data) return null

  const costsStr = Object.entries(data.identifier.costs)
    .map(([key, value]) => `${key}=${fmtNum(value, 2)}`)
    .join(", ")

  return (
    <div className="flex flex-col gap-6">
      {/* A/B */}
      <div>
        <p className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          {t("sections.ab")}
        </p>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <KpiCard
            label="L2 Pass (closed)"
            value={fmtPct(data.ab.l2PassClosed)}
            invert
          />
          <KpiCard label="L2 Pass (open)" value={fmtPct(data.ab.l2PassOpen)} />
          <KpiCard
            label={t("kpis.mentorHoursSaved")}
            value={fmtNum(data.ab.mentorHoursSaved)}
            sub={t("kpis.mentorHoursSub")}
          />
        </div>
      </div>

      {/* Cohort */}
      <div>
        <p className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          {t("sections.cohort")}
        </p>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-2">
          <KpiCard
            label="Pooled Reach Rate"
            value={fmtPct(data.cohort.pooledReachRate)}
            invert
          />
          <KpiCard label="N (cohort)" value={data.cohort.pooledN} />
        </div>
      </div>

      {/* Identifier */}
      <div>
        <p className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          {t("sections.identifier")}
        </p>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <KpiCard
            label={t("kpis.jOptimalTk")}
            value={fmtNum(data.identifier.jOptimalTk, 0)}
            sub={t("kpis.jOptimalSub", { costs: costsStr })}
            invert
          />
          <KpiCard
            label="Recall at opt"
            value={fmtPct(data.identifier.recallAtOpt)}
          />
        </div>
      </div>

      {/* Ops */}
      <div>
        <p className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          {t("sections.ops")}
        </p>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <KpiCard
            label={t("kpis.activeSessions")}
            value={data.ops.activeSessions}
            invert
          />
          <KpiCard
            label={t("kpis.totalInterventions")}
            value={data.ops.totalInterventions}
          />
          <KpiCard
            label={t("kpis.finishedSessionsN")}
            value={data.ops.finishedSessionsN}
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => router.refresh()}
        >
          {t("refreshButton")}
        </Button>
      </div>
    </div>
  )
}
