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
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"
import type { TkSensitivity } from "../types"
import { fetchTkSensitivity } from "../actions"

function fmtNum(v: number, digits = 2): string {
  return v.toFixed(digits)
}

// Monochrome single T_k line over ratio, built per call since the label comes from translations
function getTkConfig(t: (key: string) => string): ChartConfig {
  return {
    tK: {
      label: t("seriesLabel"),
      color: "var(--foreground)",
    },
  }
}

export function TkView() {
  const t = useTranslations("dashboard.admin.tk")
  const [data, setData] = useState<TkSensitivity | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // biome-ignore lint/correctness/useExhaustiveDependencies: t is stable per locale, fetch once on mount
  useEffect(() => {
    fetchTkSensitivity()
      .then(setData)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : t("errorFallback"))
      )
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-48 w-full" />
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

  if (!data || data.points.length === 0) {
    return (
      <div className="flex flex-col gap-4">
        <CostsBlock costs={data?.costs ?? {}} t={t} />
        <p className="text-sm text-muted-foreground">{t("emptyData")}</p>
      </div>
    )
  }

  // data for Recharts
  const chartData = data.points.map((pt) => ({
    ratio: pt.ratio,
    tK: pt.tK,
  }))

  return (
    <div className="flex flex-col gap-6">
      {/* Visible costs */}
      <CostsBlock costs={data.costs} t={t} />

      {/* T_k(ratio) chart, stepped */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide">
          {t("chartHeading")}
        </h2>
        <ChartContainer config={getTkConfig(t)} height={240}>
          <LineChart
            data={chartData}
            margin={{ top: 8, right: 16, bottom: 24, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="ratio"
              tick={{ fontSize: 11 }}
              label={{
                value: t("ratioAxisLabel"),
                position: "insideBottom",
                offset: -12,
                fontSize: 11,
              }}
              height={48}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              label={{
                value: "T_k",
                angle: -90,
                position: "insideLeft",
                fontSize: 11,
              }}
              width={40}
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  labelFormatter={(v) => `ratio = ${v}`}
                  valueFormatter={(v) => fmtNum(v, 0)}
                />
              }
            />
            {/* step = stepped line reflecting the discreteness of T_k */}
            <Line
              type="stepAfter"
              dataKey="tK"
              stroke="var(--foreground)"
              strokeWidth={2}
              dot={{ r: 3, fill: "var(--foreground)" }}
              name="tK"
            />
          </LineChart>
        </ChartContainer>
        <p className="mt-1 text-xs text-muted-foreground">{t("chartNote")}</p>
      </section>

      {/* points table (a11y alternative) */}
      <div className="overflow-x-auto border">
        <table className="w-full border-collapse text-sm text-left">
          <caption className="mb-2 text-left text-xs text-muted-foreground px-4 pt-3">
            {t("tableCaption")}
          </caption>
          <thead>
            <tr className="border-b text-xs uppercase tracking-wide text-muted-foreground">
              <th className="px-4 py-3 font-medium tabular-nums">
                {t("ratioAxisLabel")}
              </th>
              <th className="px-4 py-3 text-right font-medium tabular-nums">
                T_k
              </th>
              <th className="px-4 py-3 text-right font-medium tabular-nums">
                J
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data.points.map((pt, i) => (
              <tr key={i} className="hover:bg-muted/50 transition-colors">
                <td className="px-4 py-3 tabular-nums font-mono">
                  {fmtNum(pt.ratio)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums font-mono">
                  {fmtNum(pt.tK, 0)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {fmtNum(pt.j)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Honesty note */}
      <p className="text-xs text-muted-foreground">{t("honestyNote")}</p>
    </div>
  )
}

function CostsBlock({
  costs,
  t,
}: {
  costs: Record<string, number>
  t: (key: string) => string
}) {
  const entries = Object.entries(costs)
  return (
    <div className="border p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
        {t("costsTitle")}
      </p>
      {entries.length > 0 ? (
        <dl className="grid grid-cols-2 gap-x-8 gap-y-1 text-sm tabular-nums">
          {entries.map(([k, v]) => (
            <>
              <dt
                key={`dt-${k}`}
                className="text-muted-foreground font-mono text-xs"
              >
                {k}
              </dt>
              <dd key={`dd-${k}`} className="font-mono">
                {fmtNum(v, 3)}
              </dd>
            </>
          ))}
        </dl>
      ) : (
        <p className="text-xs text-muted-foreground">{t("costsLoading")}</p>
      )}
      <p className="mt-2 text-xs text-muted-foreground">{t("costsNote")}</p>
    </div>
  )
}
