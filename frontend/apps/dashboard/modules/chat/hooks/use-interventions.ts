"use client"

import { clientEnv } from "@repo/api/env.client"
import { fetchWsToken } from "@repo/api/realtime-token"
import { useEffect, useEffectEvent } from "react"
import type { UIMessage } from "@ai-sdk/react"

type SetMessages = (updater: (prev: UIMessage[]) => UIMessage[]) => void

const WS_BASE = clientEnv.NEXT_PUBLIC_WS_BASE_URL

export function useInterventions(
  sessionId: string,
  setMessages: SetMessages,
  onUnread?: () => void
) {
  // An effect event, so a caller can pass a fresh closure without forcing the
  // socket to reconnect.
  const notifyUnread = useEffectEvent(() => onUnread?.())

  useEffect(() => {
    let ws: WebSocket | null = null
    let closed = false
    let retry = 0

    async function connect() {
      let token: string
      try {
        token = await fetchWsToken()
      } catch {
        return
      }
      if (closed) return

      ws = new WebSocket(
        `${WS_BASE}/users/me/sessions/ws/sessions/${sessionId}?token=${token}`
      )

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === "intervention") {
            const text: string = data.content ?? ""
            if (!text) return
            setMessages((prev) => [
              ...prev,
              {
                id: `intervention-${Date.now()}`,
                role: "assistant",
                parts: [{ type: "text", text }],
              } as UIMessage,
            ])
            notifyUnread()
          }
        } catch {
          // ignore malformed frames
        }
      }

      ws.onclose = () => {
        if (closed) return
        retry += 1
        const delay = Math.min(1000 * 2 ** retry, 15000)
        setTimeout(connect, delay)
      }
    }

    connect()

    return () => {
      closed = true
      ws?.close()
    }
  }, [sessionId, setMessages])
}
