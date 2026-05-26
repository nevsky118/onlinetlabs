"use client"

import type { UIMessage } from "@ai-sdk/react"
import { useEffect } from "react"

type SetMessages = (updater: (prev: UIMessage[]) => UIMessage[]) => void

const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE_URL || "ws://localhost:8000"

export function useInterventions(
  sessionId: string,
  setMessages: SetMessages,
  onUnread?: () => void
) {
  useEffect(() => {
    let ws: WebSocket | null = null
    let closed = false
    let retry = 0

    async function connect() {
      const res = await fetch("/api/ws-token")
      if (!res.ok) return
      const { token } = (await res.json()) as { token: string }
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
            onUnread?.()
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
  }, [sessionId, setMessages, onUnread])
}
