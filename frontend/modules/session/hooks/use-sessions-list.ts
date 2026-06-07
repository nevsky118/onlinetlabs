"use client"

import { useQuery } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import type { Session } from "../types"
import { sessionsListQuery } from "../query"

const ACTIVE_STATUSES = new Set(["active", "provisioning"])

function hasActive(sessions: Session[]): boolean {
  return sessions.some((s) => ACTIVE_STATUSES.has(s.status))
}

export function useSessionsList() {
  const { data, refetch } = useQuery({
    ...sessionsListQuery(),
    refetchInterval: (query) =>
      hasActive(query.state.data ?? []) ? 10_000 : false,
  })
  const sessions = data ?? []

  const [tick, setTick] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(id)
  }, [])

  return { sessions, tick, refresh: refetch }
}
