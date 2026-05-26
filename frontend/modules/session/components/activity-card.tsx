"use client"

import { useActivityFeed } from "../hooks/use-activity-feed"
import { labelForEvent } from "../lib/event-labels"
import { Button } from "@/ui/button"
import { Skeleton } from "@/ui/skeleton"

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })
}

export function ActivityCard({ sessionId }: { sessionId: string }) {
  const { events, hasMore, loading, loadMore } = useActivityFeed(sessionId)

  return (
    <div className="bg-card border p-4">
      <div className="text-muted-foreground mb-3 text-xs tracking-wide uppercase">
        Активность
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
          Событий нет
        </div>
      )}
      <ul className="flex flex-col gap-2 text-sm">
        {events.map((e, i) => (
          <li key={`${e.timestamp}-${i}`} className="flex gap-3">
            <span className="text-muted-foreground w-16 shrink-0 font-mono text-xs">
              {formatTime(e.timestamp)}
            </span>
            <span>{labelForEvent(e.eventType)}</span>
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
          Показать ещё
        </Button>
      )}
    </div>
  )
}
