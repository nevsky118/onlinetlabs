"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { Session } from "../types"
import { fetchSessionsList } from "../actions"

const ACTIVE_STATUSES = new Set(["active", "provisioning"])
const POLL_INTERVAL_MS = 10_000

function hasActive(sessions: Session[]): boolean {
  return sessions.some((s) => ACTIVE_STATUSES.has(s.status))
}

function mergeById(prev: Session[], next: Session[]): Session[] {
  return next
}

export function useSessionsList(initial: Session[]) {
  const [sessions, setSessions] = useState<Session[]>(initial)
  const [tick, setTick] = useState(0)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // тик раз в секунду для живого аптайма
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(id)
  }, [])

  const refresh = useCallback(async () => {
    try {
      const next = await fetchSessionsList()
      setSessions((prev) => mergeById(prev, next))
    } catch {
      // молча оставляем устаревшие данные
    }
  }, [])

  // поллинг только пока есть активные/готовящиеся сессии
  useEffect(() => {
    if (!hasActive(sessions)) {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
      return
    }
    if (!pollRef.current) {
      pollRef.current = setInterval(refresh, POLL_INTERVAL_MS)
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [sessions, refresh])

  return { sessions, tick, refresh }
}
