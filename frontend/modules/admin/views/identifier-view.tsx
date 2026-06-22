"use client"

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
import { Alert, AlertDescription, AlertTitle } from "@/ui/alert"
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/ui/chart"
import { Skeleton } from "@/ui/skeleton"

type Props = {
  data: IdentifierEval | null
  error?: string | null
}

function fmtPct(v: number | null): string {
  if (v == null) return "—"
  return `${(v * 100).toFixed(1)}%`
}

function fmtNum(v: number | null, digits = 3): string {
  if (v == null) return "—"
  return v.toFixed(digits)
}

// Конфиг серий — монохром: recall сплошная тёмная, falsePerHour пунктир светлее
const curveConfig: ChartConfig = {
  recall: {
    label: "Recall (сплошная)",
    color: "var(--chart-5)",
    dash: undefined,
  },
  falsePerHour: {
    label: "False/ч (пунктир)",
    color: "var(--chart-3)",
    dash: "4 2",
  },
}

export function IdentifierView({ data, error }: Props) {
  if (error) {
    return (
      <Alert>
        <AlertTitle>Ошибка загрузки</AlertTitle>
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

  // Данные для Recharts — recall нормированный [0,1], falsePerHour масштабировать не нужно
  const chartData = data.curve.map((row) => ({
    tK: row.tK,
    recall: row.recall,
    falsePerHour: row.falsePerHour,
  }))

  return (
    <div className="flex flex-col gap-8">
      {/* Подзаголовок + «предварительно» + honesty */}
      <div className="flex flex-col gap-1">
        <p className="text-xs text-muted-foreground">
          rate&gt;F1; заменяет внешние PoC
        </p>
        {data.preliminary && (
          <span className="inline-block border border-foreground px-2 py-0.5 text-xs font-medium uppercase tracking-wide">
            ПРЕДВАРИТЕЛЬНО
          </span>
        )}
      </div>

      {/* Operating-кривая CHART */}
      {chartData.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide">
            Operating-кривая (график)
          </h2>
          <ChartContainer config={curveConfig} height={280}>
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
                    labelFormatter={(v) => `T_k = ${v}`}
                    valueFormatter={(v, name) =>
                      name === "recall" ? fmtPct(v) : fmtNum(v, 2)
                    }
                  />
                }
              />
              <ChartLegend content={<ChartLegendContent />} />
              {/* J-оптимум как вертикальная метка */}
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
          <p className="mt-1 text-xs text-muted-foreground">
            Recall — сплошная; False/ч — пунктир. J-оптимум — вертикальная
            метка.
          </p>
        </section>
      )}

      {/* Operating-кривая TABLE (a11y-альтернатива) */}
      {data.curve.length === 0 ? (
        <p className="text-sm text-muted-foreground">Нет данных кривой</p>
      ) : (
        <section>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide">
            Operating-кривая (таблица)
          </h2>
          <div className="overflow-x-auto border">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-3 font-medium">T_k</th>
                  <th className="px-4 py-3 text-right font-medium">
                    Latency med.
                  </th>
                  <th className="px-4 py-3 text-right font-medium">False/ч</th>
                  <th className="px-4 py-3 text-right font-medium">Recall</th>
                  <th className="px-4 py-3 text-right font-medium">J</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.curve.map((row, i) => {
                  const isOpt = row.tK === data.jOptimalTk
                  return (
                    <tr
                      key={i}
                      className={
                        isOpt
                          ? "bg-foreground text-background font-bold"
                          : "hover:bg-muted/50 transition-colors"
                      }
                    >
                      <td className="px-4 py-3 tabular-nums font-mono">
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
            J-оптимум (T_k={fmtNum(data.jOptimalTk, 0)}) выделен инверсом
          </p>
        </section>
      )}

      {/* Матрица путаницы */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide">
          Матрица путаницы
        </h2>
        <ConfusionGrid confusion={data.confusion} />
      </section>

      {/* First-match числа */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide">
          First-match диагностика
        </h2>
        <p className="mb-2 text-xs text-muted-foreground">
          rate-метрики приоритетнее F1
        </p>
        <div className="flex flex-col gap-2 border p-4 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Multi-match rate</span>
            <span className="tabular-nums font-medium">
              {fmtPct(data.firstMatch.multiMatchRate)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Order-sensitive rate</span>
            <span className="tabular-nums font-medium">
              {fmtPct(data.firstMatch.orderSensitiveRate)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">
              Всего firing-снапшотов
            </span>
            <span className="tabular-nums font-medium">
              {data.firstMatch.totalFiringSnapshots}
            </span>
          </div>
        </div>
      </section>

      {/* Стоимости */}
      {Object.keys(data.costs).length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide">
            Стоимости
          </h2>
          <div className="flex flex-col gap-1 border p-4 text-sm">
            {Object.entries(data.costs).map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className="text-muted-foreground font-mono text-xs">
                  {k}
                </span>
                <span className="tabular-nums">{fmtNum(v, 2)}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
