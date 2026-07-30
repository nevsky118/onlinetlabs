"use client"

// Canonical shadcn chart.tsx, a monochrome wrapper around Recharts
import * as React from "react"
import { Legend, ResponsiveContainer, Tooltip } from "recharts"

// --- ChartConfig -------------------------------------------------------

export type ChartConfig = Record<
  string,
  {
    label?: string
    // color token, e.g. "var(--chart-1)". Monochrome.
    color?: string
    // strokeDasharray for the series, e.g. "4 2"
    dash?: string
  }
>

// --- Context -----------------------------------------------------------

type ChartContextValue = { config: ChartConfig }
const ChartContext = React.createContext<ChartContextValue | null>(null)

export function useChart(
  errorOutsideProvider = "useChart must be used within a ChartContainer"
) {
  const ctx = React.useContext(ChartContext)
  if (!ctx) throw new Error(errorOutsideProvider)
  return ctx
}

// --- ChartContainer ----------------------------------------------------

interface ChartContainerProps {
  config: ChartConfig
  children: React.ReactElement
  className?: string
  /** container height, 300 by default */
  height?: number
}

export function ChartContainer({
  config,
  children,
  className,
  height = 300,
}: ChartContainerProps) {
  // CSS variables for the tokens are passed inline
  const cssVars = Object.fromEntries(
    Object.entries(config).map(([key, val]) => [
      `--color-${key}`,
      val.color ?? `var(--foreground)`,
    ])
  ) as React.CSSProperties

  return (
    <ChartContext.Provider value={{ config }}>
      <div className={className} style={{ ...cssVars, width: "100%" }}>
        <ResponsiveContainer width="100%" height={height}>
          {children}
        </ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  )
}

// --- ChartTooltip / ChartTooltipContent --------------------------------

/** Proxy to the Recharts Tooltip, pass content={<ChartTooltipContent />} */
export const ChartTooltip = Tooltip

export interface ChartTooltipContentProps {
  active?: boolean
  payload?: Array<{ name: string; value: number; color?: string }>
  label?: string | number
  labelFormatter?: (label: string | number) => string
  valueFormatter?: (value: number, name: string) => string
  errorOutsideProvider?: string
}

export function ChartTooltipContent({
  active,
  payload,
  label,
  labelFormatter,
  valueFormatter,
  errorOutsideProvider,
}: ChartTooltipContentProps) {
  const { config } = useChart(errorOutsideProvider)
  if (!active || !payload?.length) return null

  return (
    <div className="border bg-background px-3 py-2 text-xs shadow-sm">
      {label != null && (
        <p className="mb-1 font-medium tabular-nums">
          {labelFormatter ? labelFormatter(label) : String(label)}
        </p>
      )}
      <dl className="flex flex-col gap-0.5">
        {payload.map((entry) => {
          const cfg = config[entry.name]
          const displayName = cfg?.label ?? entry.name
          const val = valueFormatter
            ? valueFormatter(entry.value, entry.name)
            : String(entry.value)
          return (
            <div key={entry.name} className="flex items-center gap-2">
              <span
                className="inline-block h-2 w-4 shrink-0"
                style={{
                  background: cfg?.color ?? "var(--foreground)",
                  opacity: cfg?.dash ? 0.6 : 1,
                }}
              />
              <dt className="text-muted-foreground">{displayName}</dt>
              <dd className="ml-auto tabular-nums font-medium">{val}</dd>
            </div>
          )
        })}
      </dl>
    </div>
  )
}

// --- ChartLegend / ChartLegendContent ----------------------------------

/** Proxy to the Recharts Legend */
export const ChartLegend = Legend

export interface ChartLegendContentProps {
  payload?: Array<{ value: string; color?: string }>
  errorOutsideProvider?: string
}

export function ChartLegendContent({
  payload,
  errorOutsideProvider,
}: ChartLegendContentProps) {
  const { config } = useChart(errorOutsideProvider)
  if (!payload?.length) return null

  return (
    <ul className="flex flex-wrap gap-4 px-2 text-xs text-muted-foreground">
      {payload.map((entry) => {
        const cfg = config[entry.value]
        return (
          <li key={entry.value} className="flex items-center gap-1.5">
            {/* swatch line, color plus a dashed line if dash is set */}
            <svg width={24} height={8} aria-hidden="true">
              <line
                x1="0"
                y1="4"
                x2="24"
                y2="4"
                stroke={cfg?.color ?? "var(--foreground)"}
                strokeWidth={2}
                strokeDasharray={cfg?.dash}
              />
            </svg>
            <span>{cfg?.label ?? entry.value}</span>
          </li>
        )
      })}
    </ul>
  )
}
