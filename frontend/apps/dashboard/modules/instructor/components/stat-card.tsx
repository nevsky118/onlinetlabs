import { cn } from "@repo/design-system/lib/utils"
import type { ReactNode } from "react"

interface StatCardProps {
  label: string
  value: ReactNode
  hint?: string
  className?: string
}

export function StatCard({ label, value, hint, className }: StatCardProps) {
  return (
    <div className={cn("flex flex-col gap-1 border p-4", className)}>
      <span className="text-xs tracking-wide text-muted-foreground uppercase">
        {label}
      </span>
      <span className="text-2xl font-semibold tabular-nums">{value}</span>
      {hint ? (
        <span className="text-xs text-muted-foreground">{hint}</span>
      ) : null}
    </div>
  )
}
