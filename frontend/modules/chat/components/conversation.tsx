"use client"

import type { UIMessage } from "@ai-sdk/react"
import type { CSSProperties, ReactNode } from "react"
import type { AgentActivityEvent } from "../types"
import { ChatMessages } from "./chat-messages"
import { cn } from "@/lib/utils"

// Точечный фон — общая поверхность разговора.
const DOT_BG: CSSProperties = {
  backgroundImage:
    "radial-gradient(circle, color-mix(in oklab, var(--color-foreground) 8%, transparent) 1px, transparent 1px)",
  backgroundSize: "12px 12px",
}

// Переиспользуемая поверхность чата: рамка + шапка-слот + лента сообщений
// (с встроенными событиями логов) + опциональный футер (инпут). Один и тот же
// рендер для боевого чата и read-only просмотра у инструктора.
export function Conversation({
  header,
  messages,
  events,
  footer,
  emptyState,
  className,
}: {
  header?: ReactNode
  messages: UIMessage[]
  events?: AgentActivityEvent[]
  footer?: ReactNode
  emptyState?: ReactNode
  className?: string
}) {
  return (
    <div
      className={cn("bg-background flex min-h-0 flex-1 flex-col", className)}
    >
      {header ? (
        <header className="flex shrink-0 items-center justify-between gap-2 border-b p-3.5">
          {header}
        </header>
      ) : null}
      <div className="relative flex min-h-0 flex-1 flex-col">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          style={DOT_BG}
        />
        {messages.length === 0 && emptyState ? (
          emptyState
        ) : (
          <ChatMessages messages={messages} events={events} />
        )}
        {footer}
      </div>
    </div>
  )
}
