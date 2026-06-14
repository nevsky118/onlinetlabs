import { CheckCircle2 } from "lucide-react"
import type { LabProgress } from "../types"
import { cn } from "@/lib/utils"
import { Badge } from "@/ui/badge"

function formatScore(score: number | null): string | null {
  return score === null ? null : `${Math.round(score)}`
}

export function LabProgressBadge({
  progress,
  className,
}: {
  progress: LabProgress | null
  className?: string
}) {
  if (!progress || progress.status === "not_started") return null

  const score = formatScore(progress.score)

  if (progress.status === "completed") {
    return (
      <Badge className={cn("gap-1", className)}>
        <CheckCircle2 data-icon="inline-start" />
        Завершено{score !== null ? ` · ${score}` : ""}
      </Badge>
    )
  }

  // in_progress: показываем балл только если уже что-то набрано
  return (
    <Badge variant="secondary" className={className}>
      В процессе{score !== null && score !== "0" ? ` · ${score}` : ""}
    </Badge>
  )
}
