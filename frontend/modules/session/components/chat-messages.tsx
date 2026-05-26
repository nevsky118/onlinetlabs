"use client"

import type { UIMessage } from "@ai-sdk/react"
import { useEffect, useRef } from "react"
import { ChatResponse } from "./chat-response"
import { cn } from "@/lib/utils"

function messageText(m: UIMessage): string {
  return m.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("")
}

export function ChatMessages({ messages }: { messages: UIMessage[] }) {
  const endRef = useRef<HTMLDivElement>(null)

  // biome-ignore lint/correctness/useExhaustiveDependencies: автоскролл к низу при появлении новых сообщений
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-3">
      {messages.map((m) => (
        <div
          key={m.id}
          className={cn(
            "max-w-[85%] rounded-lg px-3 py-2 text-sm",
            m.role === "user"
              ? "self-end bg-primary text-primary-foreground"
              : "self-start bg-muted text-foreground"
          )}
        >
          {m.role === "assistant" ? (
            <ChatResponse>{messageText(m)}</ChatResponse>
          ) : (
            messageText(m)
          )}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  )
}
