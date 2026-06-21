"use client"

import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import type { Overview } from "../types"
import { fetchOverview } from "../actions"
import { KpiCard } from "../components/kpi-card"
import { Alert, AlertDescription, AlertTitle } from "@/ui/alert"
import { Button } from "@/ui/button"
import { Skeleton } from "@/ui/skeleton"

function fmtPct(v: number): string {
  return `${(v * 100).toFixed(1)}%`
}

function fmtNum(v: number, digits = 1): string {
  return v.toFixed(digits)
}

// Сетка KPI-карточек для раздела «Обзор»
export function OverviewView() {
  const router = useRouter()
  const [data, setData] = useState<Overview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOverview()
      .then(setData)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Ошибка загрузки")
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Alert>
        <AlertTitle>Ошибка</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!data) return null

  const costsStr = Object.entries(data.identifier.costs)
    .map(([k, v]) => `${k}=${fmtNum(v, 2)}`)
    .join(", ")

  return (
    <div className="flex flex-col gap-6">
      {/* A/B */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          A/B
        </p>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <KpiCard
            label="L2 Pass (closed)"
            value={fmtPct(data.ab.l2PassClosed)}
            invert
          />
          <KpiCard label="L2 Pass (open)" value={fmtPct(data.ab.l2PassOpen)} />
          <KpiCard
            label="Ч. наставника сохранено"
            value={fmtNum(data.ab.mentorHoursSaved)}
            sub="контрфактуал A/B"
          />
        </div>
      </div>

      {/* Когорта */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Когорта
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

      {/* Идентификатор */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Идентификатор
        </p>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <KpiCard
            label="J-оптимальный T_k"
            value={fmtNum(data.identifier.jOptimalTk, 0)}
            sub={`при стоимостях: ${costsStr}`}
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
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Ops
        </p>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <KpiCard
            label="Активных сессий"
            value={data.ops.activeSessions}
            invert
          />
          <KpiCard
            label="Интервенций всего"
            value={data.ops.totalInterventions}
          />
          <KpiCard label="Реальная разметка N" value={data.ops.labeledRealN} />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => router.refresh()}
        >
          Обновить
        </Button>
      </div>
    </div>
  )
}
