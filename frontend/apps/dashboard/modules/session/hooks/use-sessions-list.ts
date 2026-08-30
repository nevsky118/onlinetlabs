"use client"

import { useQuery } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import type { Session } from "../types"
import { sessionsListQuery } from "../query"

const ACTIVE_STATUSES = new Set(["active", "provisioning"])
const UPTIME_TICK_MS = 1000

function hasActive(sessions: Session[]): boolean {
  return sessions.some((session) => ACTIVE_STATUSES.has(session.status))
}

export function useSessionsList() {
  const { data, refetch } = useQuery({
    ...sessionsListQuery(),
    refetchInterval: (query) =>
      hasActive(query.state.data ?? []) ? 10_000 : false,
  })
  const sessions = data ?? []

  // A clock in state, not Date.now() during render, so uptime stays a pure
  // function of the rendered value.
  const [nowMs, setNowMs] = useState(() => Date.now())
  useEffect(() => {
    const intervalId = setInterval(() => setNowMs(Date.now()), UPTIME_TICK_MS)
    return () => clearInterval(intervalId)
  }, [])

  return { sessions, nowMs, refresh: refetch }
}
