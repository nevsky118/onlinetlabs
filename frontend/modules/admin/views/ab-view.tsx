"use client"

import type { ArmAnalysis } from "../types"

function fmtPct(v: number): string {
  return `${(v * 100).toFixed(1)}%`
}

function fmtNum(v: number, digits = 3): string {
  return v.toFixed(digits)
}

function AbSkeleton() {
  return (
    <div
      role="status"
      className="flex flex-col gap-6"
      aria-busy="true"
      aria-label="Загрузка A/B-эффекта"
    >
      <div className="h-6 w-48 bg-muted animate-pulse" />
      <div className="h-32 w-full bg-muted animate-pulse" />
      <div className="h-20 w-full bg-muted animate-pulse" />
    </div>
  )
}

function AbEmpty() {
  return (
    <p className="text-sm text-muted-foreground py-6">
      Нет данных A/B-анализа. Убедитесь, что эксперимент проведён и метрики
      собраны.
    </p>
  )
}

interface AbViewProps {
  data: ArmAnalysis | null
  loading?: boolean
  error?: string | null
}

export function AbView({ data, loading, error }: AbViewProps) {
  if (loading) return <AbSkeleton />

  if (error) {
    return (
      <div role="alert" className="border border-foreground p-4 text-sm">
        <strong>Ошибка:</strong> {error}
      </div>
    )
  }

  if (!data) return <AbEmpty />

  const delta = (a: number, b: number) => fmtPct(a - b)

  return (
    <div className="flex flex-col gap-8">
      {/* Таблица closed↔open */}
      <div className="overflow-x-auto border">
        <table
          className="w-full border-collapse text-sm"
          aria-label="Сравнение плеч A/B"
        >
          <thead>
            <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
              <th className="px-4 py-3 font-medium">Метрика</th>
              <th className="px-4 py-3 text-right font-medium">Closed</th>
              <th className="px-4 py-3 text-right font-medium">Open</th>
              <th className="px-4 py-3 text-right font-medium">
                Δ (closed − open)
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            <tr className="hover:bg-muted/50 transition-colors">
              <td className="px-4 py-3">L2 Pass Rate</td>
              <td className="px-4 py-3 text-right tabular-nums font-medium">
                {fmtPct(data.l2PassRateClosed)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums">
                {fmtPct(data.l2PassRateOpen)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums font-medium">
                {delta(data.l2PassRateClosed, data.l2PassRateOpen)}
              </td>
            </tr>
            <tr className="hover:bg-muted/50 transition-colors">
              <td className="px-4 py-3">Эскалации (ср.)</td>
              <td className="px-4 py-3 text-right tabular-nums">
                {fmtNum(data.escalationsMeanClosed)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums">
                {fmtNum(data.escalationsMeanOpen)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums">
                {fmtNum(data.escalationsMeanClosed - data.escalationsMeanOpen)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* repeated_errors_comparison числа */}
      {Object.keys(data.repeatedErrorsComparison).length > 0 && (
        <div className="overflow-x-auto border">
          <table
            className="w-full border-collapse text-sm"
            aria-label="Повторные ошибки"
          >
            <thead>
              <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
                <th className="px-4 py-3 font-medium">Ключ</th>
                <th className="px-4 py-3 text-right font-medium">Значение</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {Object.entries(data.repeatedErrorsComparison).map(([k, v]) => (
                <tr key={k} className="hover:bg-muted/50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs">{k}</td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {typeof v === "number" ? fmtNum(v) : String(v)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Контрфактуал: часы наставника */}
      <div className="border p-4 flex flex-col gap-2">
        <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">
          Ч. наставника сохранено
        </p>
        <p className="tabular-nums font-mono text-2xl font-semibold">
          {fmtNum(data.mentorHoursSaved, 1)} ч
        </p>
        <p className="text-xs text-muted-foreground">
          контрфактуал A/B — δ = closed − open интерпретируется как экономия
        </p>
      </div>

      {/* Honesty-подпись */}
      <p className="text-xs text-muted-foreground border-t pt-4">
        Дельта плеч <strong>каузальна</strong> (рандомизация) — это раздел, где
        допустима каузальная интерпретация.
      </p>
    </div>
  )
}
