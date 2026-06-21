import { Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from "recharts"
import type { CohortCell, CohortMetrics } from "@/modules/instructor/types"
import { Alert, AlertDescription, AlertTitle } from "@/ui/alert"
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/ui/chart"
import { Separator } from "@/ui/separator"
import { Skeleton } from "@/ui/skeleton"

// секунды → дни, 1 знак
function fmtDays(seconds: number | null): string {
  if (seconds === null) return "—"
  return (seconds / 86400).toFixed(1)
}

// reach rate → %
function fmtPct(rate: number | null): string {
  if (rate === null) return "—"
  return `${(rate * 100).toFixed(1)}%`
}

// среднее число вмешательств
function fmtNum(v: number | null): string {
  if (v === null) return "—"
  return v.toFixed(2)
}

// медиана (дни) или reach@T как fallback при <50% достигших
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
  const label = row.skill ?? "Все навыки"
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

// Монохром-конфиг для BarChart reach-rate
const barConfig: ChartConfig = {
  reachRate: {
    label: "Reach L2 (%)",
    color: "var(--foreground)",
  },
}

interface CohortViewProps {
  metrics: CohortMetrics | null
  error?: string | null
}

export function CohortView({ metrics, error }: CohortViewProps) {
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Ошибка загрузки</AlertTitle>
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

  // Данные для BarChart: только bySkill с известным именем + reach rate
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
          Headline-плечо:{" "}
          <span className="font-mono">{metrics.headlineArm}</span> (closed);
          open/pooled — контекст; каузальная дельта — раздел A/B
        </p>
      ) : null}

      {/* BarChart reach-rate по навыкам */}
      {barData.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide">
            Reach L2 по навыкам (%)
          </h2>
          <ChartContainer config={barConfig} height={220}>
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
          <p className="mt-1 text-xs text-muted-foreground">
            Монохром: столбцы различаются опасностью — темнее = выше индекс
            навыка.
          </p>
        </section>
      )}

      {/* Таблица когорт (a11y-альтернатива) */}
      <div className="overflow-x-auto border">
        <table
          className="w-full border-collapse text-sm"
          aria-label="Когортные метрики по навыкам"
        >
          <thead>
            <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
              <th className="px-4 py-3 font-medium">Скилл</th>
              <th className="px-4 py-3 text-right font-medium">N</th>
              <th className="px-4 py-3 text-right font-medium">Reach L2</th>
              <th className="px-4 py-3 text-right font-medium">Цензур.</th>
              <th className="px-4 py-3 text-right font-medium">
                Медиана, дн (или reach@T)
              </th>
              <th className="px-4 py-3 text-right font-medium">
                Автономия L2-холдаут
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
                  Нет данных
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

      {/* Сводная строка «Все навыки» */}
      <div className="overflow-x-auto border">
        <table
          className="w-full border-collapse text-sm"
          aria-label="Пул всех навыков"
        >
          <tbody>
            <CohortRow row={metrics.pooled} isPooled />
          </tbody>
        </table>
      </div>

      {/* Honesty-подписи */}
      <div className="flex flex-col gap-1 text-xs text-muted-foreground">
        <p>
          KM-медиана: survivorship-bias (только записанные). При &lt;50%
          достигших — показывается reach@T/restricted-mean, не пусто и не ∞.
        </p>
        <p>
          Headline = closed. Open/pooled — контекст; каузальная дельта плеч —
          раздел A/B.
        </p>
        <p>
          <strong>Автономия L2-холдаут</strong> = вмешательства на near-transfer
          холдауте (тот же навык, новый экземпляр, open-loop оба плеча) — НЕ по
          ходу L1-обучения.
        </p>
      </div>
    </div>
  )
}
