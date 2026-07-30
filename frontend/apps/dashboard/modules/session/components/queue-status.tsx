"use client"

import { useTranslations } from "next-intl"
import { useQueuePosition } from "../hooks/use-queue-position"

export function QueueStatus({ labSlug }: { labSlug: string }) {
  const t = useTranslations("dashboard.session.queueStatus")
  const durationT = useTranslations("dashboard.session.duration")
  const status = useQueuePosition(labSlug)
  if (!status?.inQueue) return null
  const mins = Math.max(1, Math.ceil(status.etaSec / 60))
  return (
    <div className="bg-card text-card-foreground border p-4">
      <div className="text-muted-foreground mb-2 text-xs tracking-wide uppercase">
        {t("heading")}
      </div>
      <div className="text-sm">
        {t.rich("position", {
          position: () => (
            <span className="font-medium tabular-nums">{status.position}</span>
          ),
          depth: () => (
            <span className="font-medium tabular-nums">{status.depth}</span>
          ),
        })}
      </div>
      <div className="text-muted-foreground mt-1 text-xs">
        {t("waiting", { eta: durationT("aboutMinutes", { count: mins }) })}
      </div>
    </div>
  )
}
