"use client"

import { useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import type { FullSessionState, StreamStatus, WSEvent } from "../types"
import { sessionKeys } from "../query"
import { fetchBackendToken } from "@/lib/realtime-token"

const BASE_WS_URL =
  process.env.NEXT_PUBLIC_BACKEND_WS_URL ?? "ws://localhost:8000"

function backoffMs(attempt: number): number {
  if (attempt === 0) return 1000
  return Math.min(30000, 1000 * 2 ** attempt)
}

export function useSessionRealtime(sessionId: string) {
  const qc = useQueryClient()
  const [streamStatus, setStreamStatus] = useState<StreamStatus>("connecting")
  const [wsHealthy, setWsHealthy] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const attemptRef = useRef(0)
  const stoppedRef = useRef(false)

  useEffect(() => {
    stoppedRef.current = false
    attemptRef.current = 0
    const key = sessionKeys.state(sessionId)

    const patch = (fn: (s: FullSessionState) => FullSessionState) => {
      qc.setQueryData<FullSessionState>(key, (prev) => (prev ? fn(prev) : prev))
    }
    const invalidate = () => {
      qc.invalidateQueries({ queryKey: key })
    }

    const applyEvent = (ev: WSEvent) => {
      switch (ev.type) {
        case "snapshot":
          invalidate()
          break
        case "node.status_changed":
          patch((s) => ({
            ...s,
            nodes: s.nodes.map((n) =>
              n.id === ev.payload.nodeId
                ? { ...n, status: ev.payload.status }
                : n
            ),
          }))
          break
        case "session.status_changed":
          patch((s) => ({ ...s, status: ev.payload.status }))
          break
        case "metrics.tick":
          patch((s) => ({ ...s, metrics: ev.payload }))
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
        ws.onmessage = (e) => {
          try {
            applyEvent(JSON.parse(e.data) as WSEvent)
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
  }, [sessionId, qc])

  return { streamStatus, wsHealthy }
}
