"use client"

import { useEffect, useRef, useState } from "react"
import type { FullSessionState, StreamStatus, WSEvent } from "../types"
import { bulkNodeAction, fetchSessionState, nodeAction } from "../actions"

const BASE_WS_URL =
  process.env.NEXT_PUBLIC_BACKEND_WS_URL ?? "ws://localhost:8000"

function backoffMs(attempt: number): number {
  if (attempt === 0) return 1000
  return Math.min(30000, 1000 * 2 ** attempt)
}

async function getToken(): Promise<string> {
  const r = await fetch("/api/auth/backend-token")
  if (!r.ok) throw new Error("token fetch failed")
  const body = (await r.json()) as { token: string }
  return body.token
}

export function useSessionState(sessionId: string, initial: FullSessionState) {
  const [state, setState] = useState<FullSessionState>(initial)
  const [streamStatus, setStreamStatus] = useState<StreamStatus>("connecting")
  const wsRef = useRef<WebSocket | null>(null)
  const attemptRef = useRef(0)
  const stoppedRef = useRef(false)
  const pollTimerRef = useRef<number | null>(null)

  useEffect(() => {
    stoppedRef.current = false

    const refetchState = () => {
      fetchSessionState(sessionId)
        .then(setState)
        .catch(() => {})
    }

    const applyEvent = (ev: WSEvent) => {
      switch (ev.type) {
        case "snapshot":
          // gns3-service snapshot has snake_case fields and no lab info.
          // initialState (from backend REST) already has the canonical camelCase shape,
          // so we refresh via fetchSessionState instead of trusting the WS snapshot.
          refetchState()
          break
        case "node.status_changed":
          setState((s) => ({
            ...s,
            nodes: s.nodes.map((n) =>
              n.id === ev.payload.nodeId
                ? { ...n, status: ev.payload.status }
                : n
            ),
          }))
          break
        case "session.status_changed":
          setState((s) => ({ ...s, status: ev.payload.status }))
          break
        case "metrics.tick":
          setState((s) => ({ ...s, metrics: ev.payload }))
          break
        case "state.invalidated":
          refetchState()
          break
        case "stream.degraded":
          setStreamStatus("degraded")
          break
        case "stream.restored":
          setStreamStatus("live")
          refetchState()
          break
        case "ping":
          wsRef.current?.send(JSON.stringify({ type: "pong" }))
          break
      }
    }

    const startPolling = () => {
      if (pollTimerRef.current !== null) return
      pollTimerRef.current = window.setInterval(refetchState, 10_000)
    }

    const stopPolling = () => {
      if (pollTimerRef.current !== null) {
        window.clearInterval(pollTimerRef.current)
        pollTimerRef.current = null
      }
    }

    const connect = async () => {
      if (stoppedRef.current) return
      try {
        const token = await getToken()
        const url = `${BASE_WS_URL}/users/me/sessions/ws/${sessionId}/events?token=${encodeURIComponent(token)}`
        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => {
          attemptRef.current = 0
          stopPolling()
          setStreamStatus("live")
        }
        ws.onmessage = (e) => {
          try {
            const ev = JSON.parse(e.data) as WSEvent
            applyEvent(ev)
          } catch {
            /* ignore bad payload */
          }
        }
        ws.onclose = () => {
          if (stoppedRef.current) return
          attemptRef.current += 1
          if (attemptRef.current >= 3) {
            setStreamStatus("polling")
            startPolling()
          } else {
            setStreamStatus("connecting")
            window.setTimeout(connect, backoffMs(attemptRef.current))
          }
        }
        ws.onerror = () => {
          ws.close()
        }
      } catch {
        attemptRef.current += 1
        if (stoppedRef.current) return
        if (attemptRef.current >= 3) {
          setStreamStatus("polling")
          startPolling()
        } else {
          window.setTimeout(connect, backoffMs(attemptRef.current))
        }
      }
    }

    connect()

    return () => {
      stoppedRef.current = true
      stopPolling()
      try {
        wsRef.current?.close(1000)
      } catch {
        /* ignore */
      }
    }
  }, [sessionId])

  return {
    state,
    streamStatus,
    actions: {
      nodeAction: (nodeId: string, action: string) =>
        nodeAction(sessionId, nodeId, action),
      bulkNodeAction: (action: string) => bulkNodeAction(sessionId, action),
    },
  }
}
