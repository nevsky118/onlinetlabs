"use client"

import { Button } from "@repo/design-system/ui/button"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { useFormatter, useTranslations } from "next-intl"
import { useActivityFeed } from "../hooks/use-activity-feed"
import { labelForEvent } from "../lib/event-labels"

export function ActivityCard({ sessionId }: { sessionId: string }) {
  const t = useTranslations("dashboard.session.activityCard")
  const eventT = useTranslations("dashboard.session.eventLabels")
  const format = useFormatter()
  const { events, hasMore, loading, loadMore } = useActivityFeed(sessionId)

  return (
    <div className="bg-card border p-4">
      <div className="text-muted-foreground mb-3 text-xs tracking-wide uppercase">
        {t("heading")}
      </div>
      {events.length === 0 && loading && (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-4" />
          <Skeleton className="h-4" />
          <Skeleton className="h-4" />
        </div>
      )}
      {events.length === 0 && !loading && (
        <div className="text-muted-foreground py-4 text-center text-sm">
          {t("empty")}
        </div>
      )}
      <ul className="flex flex-col gap-2 text-sm">
        {events.map((e, i) => (
          <li key={`${e.timestamp}-${i}`} className="flex gap-3">
            <span className="text-muted-foreground w-16 shrink-0 font-mono text-xs">
              {format.dateTime(new Date(e.timestamp), {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
            <span>{labelForEvent(e.eventType, eventT)}</span>
          </li>
        ))}
      </ul>
      {hasMore && (
        <Button
          variant="outline"
          size="sm"
          className="mt-3 w-full rounded-none"
          disabled={loading}
          onClick={loadMore}
        >
          {t("loadMore")}
        </Button>
      )}
    </div>
  )
}
