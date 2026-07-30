"use client"

import { useQuery } from "@tanstack/react-query"
import { sessionStateQuery } from "../query"
import { useNodeMutations } from "./use-node-mutations"
import { useSessionRealtime } from "./use-session-realtime"

export function useSessionState(sessionId: string) {
  const { streamStatus, wsHealthy } = useSessionRealtime(sessionId)

  const { data: state } = useQuery({
    ...sessionStateQuery(sessionId),
    refetchInterval: wsHealthy ? false : 10_000,
  })

  const actions = useNodeMutations(sessionId)

  return { state, streamStatus, actions }
}
