import { cn } from "@repo/design-system/lib/utils"
import { Badge } from "@repo/design-system/ui/badge"
import { CheckCircle2 } from "lucide-react"
import { useTranslations } from "next-intl"
import type { LabProgress } from "../types"

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
  const t = useTranslations("dashboard.progress.labProgressBadge")
  if (!progress || progress.status === "not_started") return null

  const score = formatScore(progress.score)

  if (progress.status === "completed") {
    return (
      <Badge className={cn("gap-1", className)}>
        <CheckCircle2 data-icon="inline-start" />
        {t("completed")}
        {score !== null ? ` · ${score}` : ""}
      </Badge>
    )
  }

  // in_progress: show the score only if something has already been earned
  return (
    <Badge variant="secondary" className={className}>
      {t("inProgress")}
      {score !== null && score !== "0" ? ` · ${score}` : ""}
    </Badge>
  )
}
