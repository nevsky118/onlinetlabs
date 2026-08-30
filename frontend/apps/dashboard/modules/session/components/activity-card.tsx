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
    <div className="border bg-card p-4">
      <div className="mb-3 text-xs tracking-wide text-muted-foreground uppercase">
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
        <div className="py-4 text-center text-sm text-muted-foreground">
          {t("empty")}
        </div>
      )}
      <ul className="flex flex-col gap-2 text-sm">
        {events.map((event, index) => (
          <li key={`${event.timestamp}-${index}`} className="flex gap-3">
            <span className="w-16 shrink-0 font-mono text-xs text-muted-foreground">
              {format.dateTime(new Date(event.timestamp), {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
            <span>{labelForEvent(event.eventType, eventT)}</span>
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
