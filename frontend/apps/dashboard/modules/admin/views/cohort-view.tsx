"use client"

import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@repo/design-system/ui/alert"
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@repo/design-system/ui/chart"
import { Separator } from "@repo/design-system/ui/separator"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { useTranslations } from "next-intl"
import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from "recharts"
import type { CohortCell, CohortMetrics } from "@/modules/instructor/types"

// seconds → days, 1 decimal place
function fmtDays(seconds: number | null): string {
  if (seconds === null) return "—"
  return (seconds / 86400).toFixed(1)
}

// reach rate → %
function fmtPct(rate: number | null): string {
  if (rate === null) return "—"
  return `${(rate * 100).toFixed(1)}%`
}

// average number of interventions
function fmtNum(v: number | null): string {
  if (v === null) return "—"
  return v.toFixed(2)
}

// median (days) or reach@T as a fallback when fewer than 50% reached
function fmtMedianOrReachAtT(
  medianSec: number | null,
  reachRateAtHorizon: number | null,
  censored: number,
  n: number
): string {
  if (medianSec !== null) return fmtDays(medianSec)
  if (reachRateAtHorizon !== null)
    return `reach@T ${fmtPct(reachRateAtHorizon)}`
  if (n > 0 && censored / n > 0.5) return "reach@T —"
  return "—"
}

function CohortRow({ row, isPooled }: { row: CohortCell; isPooled?: boolean }) {
  const t = useTranslations("dashboard.admin.cohort")
  const label = row.skill ?? t("allSkills")
  const { timeToCompetence: ttc, autonomy } = row

  const medianDisplay = fmtMedianOrReachAtT(
    ttc.medianCalendarSeconds,
    ttc.reachRateAtHorizon,
    ttc.censored,
    ttc.n
  )

  return (
    <tr
      className={`transition-colors ${isPooled ? "bg-muted/30 font-medium" : "hover:bg-muted/50"}`}
    >
      <td className="px-4 py-3">{label}</td>
      <td className="px-4 py-3 text-right tabular-nums">{row.n}</td>
      <td className="px-4 py-3 text-right tabular-nums">
        {fmtPct(ttc.reachRate)}
      </td>
      <td className="px-4 py-3 text-right tabular-nums">{ttc.censored}</td>
      <td className="px-4 py-3 text-right tabular-nums">{medianDisplay}</td>
      <td className="px-4 py-3 text-right tabular-nums">
        {fmtNum(autonomy.meanL2Interventions)}
      </td>
    </tr>
  )
}

// Monochrome reach-rate BarChart config, built per call since the label comes from translations
function getBarConfig(t: (key: string) => string): ChartConfig {
  return {
    reachRate: {
      label: t("chartConfigLabel"),
      color: "var(--foreground)",
    },
  }
}

interface CohortViewProps {
  metrics: CohortMetrics | null
  error?: string | null
}

export function CohortView({ metrics, error }: CohortViewProps) {
  const t = useTranslations("dashboard.admin.cohort")

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>{t("errorTitle")}</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!metrics) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
    )
  }

  const allRows: CohortCell[] = [...metrics.bySkill, ...(metrics.byArm ?? [])]

  // BarChart data, only bySkill entries with a known name + reach rate
  const barData = metrics.bySkill
    .filter((r) => r.skill != null)
    .map((r) => ({
      skill: r.skill as string,
      reachRate:
        r.timeToCompetence.reachRate != null
          ? parseFloat((r.timeToCompetence.reachRate * 100).toFixed(1))
          : 0,
    }))

  return (
    <div className="flex flex-col gap-6">
      {metrics.headlineArm ? (
        <p className="text-sm text-muted-foreground">
          {t.rich("headlineText", {
            arm: () => <span className="font-mono">{metrics.headlineArm}</span>,
          })}
        </p>
      ) : null}

      {/* BarChart reach-rate by skill */}
      {barData.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide">
            {t("chartHeading")}
          </h2>
          <ChartContainer config={getBarConfig(t)} height={220}>
            <BarChart
              data={barData}
              margin={{ top: 8, right: 16, bottom: 32, left: 8 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border)"
                vertical={false}
              />
              <XAxis
                dataKey="skill"
                tick={{ fontSize: 10 }}
                angle={-30}
                textAnchor="end"
                height={56}
                interval={0}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 11 }}
                width={40}
                unit="%"
              />
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    labelFormatter={(v) => String(v)}
                    valueFormatter={(v) => `${v}%`}
                  />
                }
              />
              <Bar dataKey="reachRate" name="reachRate" radius={0}>
                {barData.map((_, idx) => (
                  <Cell
                    key={idx}
                    fill="var(--foreground)"
                    fillOpacity={
                      0.85 - idx * 0.05 < 0.4 ? 0.4 : 0.85 - idx * 0.05
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ChartContainer>
          <p className="mt-1 text-xs text-muted-foreground">{t("chartNote")}</p>
        </section>
      )}

      {/* Cohort table (a11y alternative) */}
      <div className="overflow-x-auto border">
        <table
          className="w-full border-collapse text-sm"
          aria-label={t("tableAriaLabel")}
        >
          <thead>
            <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
              <th className="px-4 py-3 font-medium">{t("headers.skill")}</th>
              <th className="px-4 py-3 text-right font-medium">N</th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.reachL2")}
              </th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.censored")}
              </th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.median")}
              </th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.autonomy")}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {allRows.length === 0 ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-6 text-center text-sm text-muted-foreground"
                >
                  {t("empty")}
                </td>
              </tr>
            ) : (
              allRows.map((row, i) => (
                <CohortRow key={`${row.skill}__${row.arm}__${i}`} row={row} />
              ))
            )}
          </tbody>
        </table>
      </div>

      <Separator />

      {/* "All skills" summary row */}
      <div className="overflow-x-auto border">
        <table
          className="w-full border-collapse text-sm"
          aria-label={t("pooledTableAriaLabel")}
        >
          <tbody>
            <CohortRow row={metrics.pooled} isPooled />
          </tbody>
        </table>
      </div>

      {/* Honesty notes */}
      <div className="flex flex-col gap-1 text-xs text-muted-foreground">
        <p>{t("honesty.km")}</p>
        <p>{t("honesty.headline")}</p>
        <p>
          {t.rich("honesty.autonomy", {
            strong: (chunks) => <strong>{chunks}</strong>,
          })}
        </p>
      </div>
    </div>
  )
}
