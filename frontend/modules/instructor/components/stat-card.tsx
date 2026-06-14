import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface StatCardProps {
  label: string
  value: ReactNode
  hint?: string
  className?: string
}

export function StatCard({ label, value, hint, className }: StatCardProps) {
  return (
    <div className={cn("flex flex-col gap-1 border p-4", className)}>
      <span className="text-muted-foreground text-xs tracking-wide uppercase">
        {label}
      </span>
      <span className="text-2xl font-semibold tabular-nums">{value}</span>
      {hint ? (
        <span className="text-muted-foreground text-xs">{hint}</span>
      ) : null}
    </div>
  )
}
