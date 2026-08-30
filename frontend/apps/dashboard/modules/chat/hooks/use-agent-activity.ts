"use client"

import { clientEnv } from "@repo/api/env.client"
import { fetchWsToken } from "@repo/api/realtime-token"
import { useEffect, useRef, useState } from "react"
import type { AgentActivityEvent } from "../types"
import { fetchAgentActivity } from "../api"
import { mapAgentActivityEvent } from "../lib/mappings"

const WS_BASE = clientEnv.NEXT_PUBLIC_WS_BASE_URL
const MAX_EVENTS = 500
const NO_EVENTS: AgentActivityEvent[] = []

export function useAgentActivity(
  sessionId: string,
  enabled: boolean
): { events: AgentActivityEvent[] } {
  const [events, setEvents] = useState<AgentActivityEvent[]>([])
  const loadedRef = useRef(false)

  useEffect(() => {
    if (!enabled) return

    let ws: WebSocket | null = null
    let closed = false
    let retry = 0

    async function init() {
      // load the history once
      if (!loadedRef.current) {
        loadedRef.current = true
        const history = await fetchAgentActivity(sessionId).catch(() => [])
        if (!closed) {
          setEvents(history.slice(-MAX_EVENTS))
        }
      }

      await connect()
    }

    async function connect() {
      let token: string
      try {
        token = await fetchWsToken()
      } catch {
        return
      }
      if (closed) return

      ws = new WebSocket(
        `${WS_BASE}/users/me/sessions/ws/observe/${sessionId}?token=${token}`
      )

      ws.onopen = () => {
        retry = 0
      }

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data as string)
          if (data.type === "agent_activity") {
            const event = mapAgentActivityEvent(data)
            setEvents((prev) => {
              const next = [...prev, event]
              return next.length > MAX_EVENTS ? next.slice(-MAX_EVENTS) : next
            })
          }
        } catch {
          // drop the broken frame
        }
      }

      ws.onclose = () => {
        if (closed) return
        retry += 1
        const delay = Math.min(1000 * 2 ** retry, 15000)
        setTimeout(connect, delay)
      }
    }

    init()

    return () => {
      closed = true
      ws?.close()
      // Reload the history the next time the toggle comes back on.
      loadedRef.current = false
    }
  }, [sessionId, enabled])

  // While the toggle is off the buffered events stay out of the render, so no
  // state has to be cleared from inside the effect.
  return { events: enabled ? events : NO_EVENTS }
}
