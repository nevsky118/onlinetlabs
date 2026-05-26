"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { ActivityEvent } from "../types"
import { fetchActivity } from "../actions"

export function useActivityFeed(sessionId: string) {
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [cursor, setCursor] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const loadedInitial = useRef(false)

  const loadMore = useCallback(async () => {
    if (!hasMore || loading) return
    setLoading(true)
    try {
      const r = await fetchActivity(sessionId, {
        limit: 20,
        cursor: cursor ?? undefined,
      })
      setEvents((prev) => [...prev, ...r.events])
      setCursor(r.nextCursor)
      setHasMore(r.nextCursor !== null)
    } catch {
      /* silent — caller can retry via loadMore */
    } finally {
      setLoading(false)
    }
  }, [sessionId, cursor, hasMore, loading])

  useEffect(() => {
    if (loadedInitial.current) return
    loadedInitial.current = true
    void loadMore()
  }, [loadMore])

  const prependEvent = useCallback((e: ActivityEvent) => {
    setEvents((prev) => {
      const key = `${e.timestamp}-${e.eventType}-${e.componentId ?? ""}`
      if (
        prev.some(
          (p) => `${p.timestamp}-${p.eventType}-${p.componentId ?? ""}` === key
        )
      )
        return prev
      return [e, ...prev]
    })
  }, [])

  return { events, hasMore, loading, loadMore, prependEvent }
}
