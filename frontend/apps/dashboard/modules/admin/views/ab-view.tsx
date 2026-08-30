"use client"

import { useTranslations } from "next-intl"
import type { ArmAnalysis } from "../types"

function fmtPct(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

function fmtNum(value: number, digits = 3): string {
  return value.toFixed(digits)
}

function AbSkeleton({ t }: { t: (key: string) => string }) {
  return (
    <div
      role="status"
      className="flex flex-col gap-6"
      aria-busy="true"
      aria-label={t("loadingAriaLabel")}
    >
      <div className="h-6 w-48 animate-pulse bg-muted" />
      <div className="h-32 w-full animate-pulse bg-muted" />
      <div className="h-20 w-full animate-pulse bg-muted" />
    </div>
  )
}

function AbEmpty({ t }: { t: (key: string) => string }) {
  return (
    <p className="py-6 text-sm text-muted-foreground">{t("emptyMessage")}</p>
  )
}

interface AbViewProps {
  data: ArmAnalysis | null
  loading?: boolean
  error?: string | null
}

export function AbView({ data, loading, error }: AbViewProps) {
  const t = useTranslations("dashboard.admin.ab")

  if (loading) return <AbSkeleton t={t} />

  if (error) {
    return (
      <div role="alert" className="border border-foreground p-4 text-sm">
        <strong>{t("errorPrefix")}</strong> {error}
      </div>
    )
  }

  if (!data) return <AbEmpty t={t} />

  const delta = (left: number, right: number) => fmtPct(left - right)

  return (
    <div className="flex flex-col gap-8">
      {/* closed↔open table */}
      <div className="overflow-x-auto border">
        <table
          className="w-full border-collapse text-sm"
          aria-label={t("tableAriaLabel")}
        >
          <thead>
            <tr className="border-b text-left text-xs tracking-wide text-muted-foreground uppercase">
              <th className="px-4 py-3 font-medium">{t("headers.metric")}</th>
              <th className="px-4 py-3 text-right font-medium">Closed</th>
              <th className="px-4 py-3 text-right font-medium">Open</th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.delta")}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            <tr className="transition-colors hover:bg-muted/50">
              <td className="px-4 py-3">{t("rows.l2PassRate")}</td>
              <td className="px-4 py-3 text-right font-medium tabular-nums">
                {fmtPct(data.l2PassRateClosed)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums">
                {fmtPct(data.l2PassRateOpen)}
              </td>
              <td className="px-4 py-3 text-right font-medium tabular-nums">
                {delta(data.l2PassRateClosed, data.l2PassRateOpen)}
              </td>
            </tr>
            <tr className="transition-colors hover:bg-muted/50">
              <td className="px-4 py-3">{t("rows.escalationsMean")}</td>
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

      {/* repeated_errors_comparison numbers */}
      {Object.keys(data.repeatedErrorsComparison).length > 0 && (
        <div className="overflow-x-auto border">
          <table
            className="w-full border-collapse text-sm"
            aria-label={t("repeatedErrorsAriaLabel")}
          >
            <thead>
              <tr className="border-b text-left text-xs tracking-wide text-muted-foreground uppercase">
                <th className="px-4 py-3 font-medium">{t("headers.key")}</th>
                <th className="px-4 py-3 text-right font-medium">
                  {t("headers.value")}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {Object.entries(data.repeatedErrorsComparison).map(
                ([key, value]) => (
                  <tr key={key} className="transition-colors hover:bg-muted/50">
                    <td className="px-4 py-3 font-mono text-xs">{key}</td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {typeof value === "number"
                        ? fmtNum(value)
                        : String(value)}
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Counterfactual, mentor hours */}
      <div className="flex flex-col gap-2 border p-4">
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          {t("mentorHours.label")}
        </p>
        <p className="font-mono text-2xl font-semibold tabular-nums">
          {fmtNum(data.mentorHoursSaved, 1)} {t("mentorHours.unit")}
        </p>
        <p className="text-xs text-muted-foreground">{t("mentorHours.note")}</p>
      </div>

      {/* Honesty note */}
      <p className="border-t pt-4 text-xs text-muted-foreground">
        {t.rich("honesty", { strong: (chunks) => <strong>{chunks}</strong> })}
      </p>
    </div>
  )
}
