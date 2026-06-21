import { cn } from "@/shared/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/ui/card"

interface KpiCardProps {
  label: string
  value: string | number
  sub?: string
  invert?: boolean
  className?: string
}

// Монохромная KPI-карточка; invert → bg-foreground text-background (акцент)
export function KpiCard({
  label,
  value,
  sub,
  invert,
  className,
}: KpiCardProps) {
  return (
    <Card
      className={cn(
        "gap-2",
        invert && "bg-foreground text-background ring-foreground",
        className
      )}
    >
      <CardHeader className="pb-0">
        <CardTitle
          className={cn(
            "text-xs font-normal uppercase tracking-widest",
            invert ? "text-background/60" : "text-muted-foreground"
          )}
        >
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        <span className="font-mono text-2xl font-semibold tabular-nums leading-none">
          {value}
        </span>
        {sub && (
          <span
            className={cn(
              "text-xs",
              invert ? "text-background/50" : "text-muted-foreground"
            )}
          >
            {sub}
          </span>
        )}
      </CardContent>
    </Card>
  )
}
