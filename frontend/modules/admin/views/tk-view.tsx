"use client"

import { useEffect, useState } from "react"
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"
import type { TkSensitivity } from "../types"
import { fetchTkSensitivity } from "../actions"
import { Alert, AlertDescription, AlertTitle } from "@/ui/alert"
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/ui/chart"
import { Skeleton } from "@/ui/skeleton"

function fmtNum(v: number, digits = 2): string {
  return v.toFixed(digits)
}

// Монохром: одна линия T_k по ratio
const tkConfig: ChartConfig = {
  tK: {
    label: "T_k (ступенчатая)",
    color: "var(--foreground)",
  },
}

export function TkView() {
  const [data, setData] = useState<TkSensitivity | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTkSensitivity()
      .then(setData)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Ошибка загрузки")
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
        <AlertTitle>Ошибка</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!data || data.points.length === 0) {
    return (
      <div className="flex flex-col gap-4">
        <CostsBlock costs={data?.costs ?? {}} />
        <p className="text-sm text-muted-foreground">Данных нет.</p>
      </div>
    )
  }

  // данные для Recharts
  const chartData = data.points.map((pt) => ({
    ratio: pt.ratio,
    tK: pt.tK,
  }))

  return (
    <div className="flex flex-col gap-6">
      {/* Видимые стоимости */}
      <CostsBlock costs={data.costs} />

      {/* График T_k(ratio) — ступенчатая */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide">
          График T_k(ratio)
        </h2>
        <ChartContainer config={tkConfig} height={240}>
          <LineChart
            data={chartData}
            margin={{ top: 8, right: 16, bottom: 24, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="ratio"
              tick={{ fontSize: 11 }}
              label={{
                value: "ratio (c_застр/c_возд)",
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
            {/* step = ступенчатая линия, отражающая дискретность T_k */}
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
        <p className="mt-1 text-xs text-muted-foreground">
          Ступенчатая форма отражает дискретность T_k.
        </p>
      </section>

      {/* Таблица points (a11y-альтернатива) */}
      <div className="overflow-x-auto border">
        <table className="w-full border-collapse text-sm text-left">
          <caption className="mb-2 text-left text-xs text-muted-foreground px-4 pt-3">
            Кривая чувствительности T_k — кривая, не число.
          </caption>
          <thead>
            <tr className="border-b text-xs uppercase tracking-wide text-muted-foreground">
              <th className="px-4 py-3 font-medium tabular-nums">
                ratio (c_застр/c_возд)
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

      {/* Honesty-подпись */}
      <p className="text-xs text-muted-foreground">
        T_k зависит от отношения c_застр/c_возд — изменение стоимостей сдвигает
        порог.
      </p>
    </div>
  )
}

function CostsBlock({ costs }: { costs: Record<string, number> }) {
  const entries = Object.entries(costs)
  return (
    <div className="border p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
        Стоимости
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
        <p className="text-xs text-muted-foreground">Загружаются...</p>
      )}
      <p className="mt-2 text-xs text-muted-foreground">
        T_k гнётся со стоимостью застревания — кривая, не одно число.
      </p>
    </div>
  )
}
