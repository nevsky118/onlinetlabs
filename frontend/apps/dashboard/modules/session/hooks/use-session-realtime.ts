"use client"

import { clientEnv } from "@repo/api/env.client"
import { fetchBackendToken } from "@repo/api/realtime-token"
import { useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import type { FullSessionState, StreamStatus, WSEvent } from "../types"
import { sessionKeys } from "../query"

const BASE_WS_URL = clientEnv.NEXT_PUBLIC_WS_BASE_URL

function backoffMs(attempt: number): number {
  if (attempt === 0) return 1000
  return Math.min(30000, 1000 * 2 ** attempt)
}

export function useSessionRealtime(sessionId: string) {
  const queryClient = useQueryClient()
  const [streamStatus, setStreamStatus] = useState<StreamStatus>("connecting")
  const [wsHealthy, setWsHealthy] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const attemptRef = useRef(0)
  const stoppedRef = useRef(false)

  useEffect(() => {
    stoppedRef.current = false
    attemptRef.current = 0
    const key = sessionKeys.state(sessionId)

    const patch = (fn: (current: FullSessionState) => FullSessionState) => {
      queryClient.setQueryData<FullSessionState>(key, (prev) =>
        prev ? fn(prev) : prev
      )
    }
    const invalidate = () => {
      queryClient.invalidateQueries({ queryKey: key })
    }

    const applyEvent = (event: WSEvent) => {
      switch (event.type) {
        case "snapshot":
          invalidate()
          break
        case "node.status_changed":
          patch((current) => ({
            ...current,
            nodes: current.nodes.map((node) =>
              node.id === event.payload.nodeId
                ? { ...node, status: event.payload.status }
                : node
            ),
          }))
          break
        case "session.status_changed":
          patch((current) => ({ ...current, status: event.payload.status }))
          break
        case "metrics.tick":
          patch((current) => ({ ...current, metrics: event.payload }))
          break
        case "state.invalidated":
          invalidate()
          break
        case "stream.degraded":
          setStreamStatus("degraded")
          break
        case "stream.restored":
          setStreamStatus("live")
          invalidate()
          break
        case "ping":
          wsRef.current?.send(JSON.stringify({ type: "pong" }))
          break
      }
    }

    const connect = async () => {
      if (stoppedRef.current) return
      try {
        const token = await fetchBackendToken()
        const url = `${BASE_WS_URL}/users/me/sessions/ws/${sessionId}/events?token=${encodeURIComponent(token)}`
        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => {
          attemptRef.current = 0
          setWsHealthy(true)
          setStreamStatus("live")
        }
        ws.onmessage = (message) => {
          try {
            applyEvent(JSON.parse(message.data) as WSEvent)
          } catch {
            /* ignore bad payload */
          }
        }
        ws.onclose = () => {
          if (stoppedRef.current) return
          setWsHealthy(false)
          attemptRef.current += 1
          if (attemptRef.current >= 3) {
            setStreamStatus("polling")
          } else {
            setStreamStatus("connecting")
            window.setTimeout(connect, backoffMs(attemptRef.current))
          }
        }
        ws.onerror = () => ws.close()
      } catch {
        setWsHealthy(false)
        attemptRef.current += 1
        if (stoppedRef.current) return
        if (attemptRef.current >= 3) {
          setStreamStatus("polling")
        } else {
          window.setTimeout(connect, backoffMs(attemptRef.current))
        }
      }
    }

    connect()

    return () => {
      stoppedRef.current = true
      try {
        wsRef.current?.close(1000)
      } catch {
        /* ignore */
      }
    }
  }, [sessionId, queryClient])

  return { streamStatus, wsHealthy }
}
