"use client"

import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@repo/design-system/ui/alert"
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@repo/design-system/ui/chart"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { useTranslations } from "next-intl"
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts"
import type { IdentifierEval } from "../types"
import { ConfusionGrid } from "../components/confusion-grid"

type Props = {
  data: IdentifierEval | null
  error?: string | null
}

function fmtPct(value: number | null): string {
  if (value == null) return "—"
  return `${(value * 100).toFixed(1)}%`
}

function fmtNum(value: number | null, digits = 3): string {
  if (value == null) return "—"
  return value.toFixed(digits)
}

// Series config, monochrome. recall is a solid dark line, falsePerHour a lighter dashed one
function getCurveConfig(t: (key: string) => string): ChartConfig {
  return {
    recall: {
      label: t("recallSolidLabel"),
      color: "var(--chart-5)",
      dash: undefined,
    },
    falsePerHour: {
      label: t("falsePerHourLabel"),
      color: "var(--chart-3)",
      dash: "4 2",
    },
  }
}

export function IdentifierView({ data, error }: Props) {
  const t = useTranslations("dashboard.admin.identifier")

  if (error) {
    return (
      <Alert>
        <AlertTitle>{t("errorTitle")}</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  // Data for Recharts. recall is normalized to [0,1], falsePerHour needs no scaling
  const chartData = data.curve.map((row) => ({
    tK: row.tK,
    recall: row.recall,
    falsePerHour: row.falsePerHour,
  }))

  return (
    <div className="flex flex-col gap-8">
      {/* Subtitle + "preliminary" + honesty */}
      <div className="flex flex-col gap-1">
        <p className="text-xs text-muted-foreground">{t("subtitle")}</p>
        {data.preliminary && (
          <span className="inline-block border border-foreground px-2 py-0.5 text-xs font-medium tracking-wide uppercase">
            {t("preliminaryBadge")}
          </span>
        )}
      </div>

      {/* Operating curve CHART */}
      {chartData.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">
            {t("sections.operatingChart")}
          </h2>
          <ChartContainer config={getCurveConfig(t)} height={280}>
            <LineChart
              data={chartData}
              margin={{ top: 24, right: 16, bottom: 8, left: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="tK"
                tick={{ fontSize: 11 }}
                label={{
                  value: "T_k",
                  position: "insideBottom",
                  offset: -4,
                  fontSize: 11,
                }}
                height={36}
              />
              <YAxis tick={{ fontSize: 11 }} width={48} />
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    labelFormatter={(value) => `T_k = ${value}`}
                    valueFormatter={(value, name) =>
                      name === "recall" ? fmtPct(value) : fmtNum(value, 2)
                    }
                  />
                }
              />
              <ChartLegend content={<ChartLegendContent />} />
              {/* J optimum as a vertical marker */}
              {data.jOptimalTk != null && (
                <ReferenceLine
                  x={data.jOptimalTk}
                  stroke="var(--foreground)"
                  strokeDasharray="2 2"
                  label={{
                    value: `T_k=${fmtNum(data.jOptimalTk, 0)}`,
                    position: "insideTopRight",
                    offset: 10,
                    fontSize: 10,
                    fill: "var(--foreground)",
                  }}
                />
              )}
              <Line
                type="monotone"
                dataKey="recall"
                stroke="var(--chart-5)"
                strokeWidth={2}
                dot={false}
                name="recall"
              />
              <Line
                type="monotone"
                dataKey="falsePerHour"
                stroke="var(--chart-3)"
                strokeWidth={2}
                strokeDasharray="4 2"
                dot={false}
                name="falsePerHour"
              />
            </LineChart>
          </ChartContainer>
          <p className="mt-1 text-xs text-muted-foreground">{t("chartNote")}</p>
        </section>
      )}

      {/* Operating curve TABLE (a11y alternative) */}
      {data.curve.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("emptyCurve")}</p>
      ) : (
        <section>
          <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">
            {t("sections.operatingTable")}
          </h2>
          <div className="overflow-x-auto border">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b text-left text-xs tracking-wide text-muted-foreground uppercase">
                  <th className="px-4 py-3 font-medium">{t("headers.tk")}</th>
                  <th className="px-4 py-3 text-right font-medium">
                    {t("headers.latencyMedian")}
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    {t("headers.falsePerHour")}
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    {t("headers.recall")}
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    {t("headers.j")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.curve.map((row, index) => {
                  const isOpt = row.tK === data.jOptimalTk
                  return (
                    <tr
                      key={index}
                      className={
                        isOpt
                          ? "bg-foreground font-bold text-background"
                          : "transition-colors hover:bg-muted/50"
                      }
                    >
                      <td className="px-4 py-3 font-mono tabular-nums">
                        {fmtNum(row.tK, 0)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {fmtNum(row.latencyMedian)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {fmtNum(row.falsePerHour, 2)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {fmtPct(row.recall)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        {fmtNum(row.j)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {t("optimumNote", { value: fmtNum(data.jOptimalTk, 0) })}
          </p>
        </section>
      )}

      {/* Confusion matrix */}
      <section>
        <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">
          {t("sections.confusionMatrix")}
        </h2>
        <ConfusionGrid confusion={data.confusion} />
      </section>

      {/* First-match numbers */}
      <section>
        <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">
          {t("sections.firstMatch")}
        </h2>
        <p className="mb-2 text-xs text-muted-foreground">
          {t("firstMatchNote")}
        </p>
        <div className="flex flex-col gap-2 border p-4 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">
              {t("rows.multiMatchRate")}
            </span>
            <span className="font-medium tabular-nums">
              {fmtPct(data.firstMatch.multiMatchRate)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">
              {t("rows.orderSensitiveRate")}
            </span>
            <span className="font-medium tabular-nums">
              {fmtPct(data.firstMatch.orderSensitiveRate)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">
              {t("rows.totalFiringSnapshots")}
            </span>
            <span className="font-medium tabular-nums">
              {data.firstMatch.totalFiringSnapshots}
            </span>
          </div>
        </div>
      </section>

      {/* Costs */}
      {Object.keys(data.costs).length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">
            {t("sections.costs")}
          </h2>
          <div className="flex flex-col gap-1 border p-4 text-sm">
            {Object.entries(data.costs).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="font-mono text-xs text-muted-foreground">
                  {key}
                </span>
                <span className="tabular-nums">{fmtNum(value, 2)}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
