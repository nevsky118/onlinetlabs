"use client"

import type { UIMessage } from "@ai-sdk/react"
import { cn } from "@repo/design-system/lib/utils"
import type { CSSProperties, ReactNode } from "react"
import type { AgentActivityEvent } from "../types"
import { ChatMessages } from "./chat-messages"

// Dotted background, the shared conversation surface.
const DOT_BG: CSSProperties = {
  backgroundImage:
    "radial-gradient(circle, color-mix(in oklab, var(--color-foreground) 8%, transparent) 1px, transparent 1px)",
  backgroundSize: "12px 12px",
}

// Reusable chat surface. Frame + header slot + message feed (with embedded log
// events) + optional footer (the input). The same render for the live chat and
// for the instructor's read-only view.
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
