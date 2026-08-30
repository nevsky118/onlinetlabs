"use client"

import { Button } from "@repo/design-system/ui/button"
import { CheckIcon, CopyIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useRef, useState } from "react"
import type { AgentActivityEvent } from "../types"
import type { UIMessage } from "@ai-sdk/react"
import { AgentActivityLine } from "./agent-activity-console"
import { ChatResponse } from "./chat-response"

function messageText(message: UIMessage): string {
  return message.parts
    .filter(
      (part): part is { type: "text"; text: string } => part.type === "text"
    )
    .map((part) => part.text)
    .join("")
}

// Message time. History carries createdAt in metadata; live messages have none,
// so we stamp them with the moment they first appeared (needed to embed logs by time).
const firstSeenAt = new Map<string, number>()

function messageTs(message: UIMessage): number {
  const meta = message.metadata as { createdAt?: string } | undefined
  if (meta?.createdAt) return Date.parse(meta.createdAt)
  let seenAt = firstSeenAt.get(message.id)
  if (seenAt === undefined) {
    seenAt = Date.now()
    firstSeenAt.set(message.id, seenAt)
  }
  return seenAt
}

function CopyButton({ text }: { text: string }) {
  const t = useTranslations("dashboard.chat.messages")
  const [copied, setCopied] = useState(false)

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-xs"
      aria-label={t("copyResponse")}
      className="text-muted-foreground hover:text-foreground"
      onClick={async () => {
        await navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 1500)
      }}
    >
      {copied ? <CheckIcon /> : <CopyIcon />}
    </Button>
  )
}

function MessageBubble({
  message,
  isLast,
}: {
  message: UIMessage
  isLast: boolean
}) {
  const text = messageText(message)
  if (message.role === "user") {
    return (
      <article
        data-sender="user"
        className="flex animate-in flex-col items-end duration-300 fade-in-0"
      >
        <div className="ml-auto w-fit max-w-[85%] bg-muted px-4 py-3 text-sm leading-relaxed break-words whitespace-pre-wrap text-foreground">
          {text}
        </div>
      </article>
    )
  }
  return (
    <article
      data-sender="ai"
      className="group/message flex animate-in flex-col items-start gap-1 duration-300 fade-in-0"
    >
      <div className="w-full max-w-full text-sm leading-relaxed">
        <ChatResponse>{text}</ChatResponse>
      </div>
      <div
        className="flex items-center opacity-0 transition-opacity duration-200 group-hover/message:opacity-100 data-[last=true]:opacity-100"
        data-last={isLast}
      >
        <CopyButton text={text} />
      </div>
    </article>
  )
}

const NO_EVENTS: AgentActivityEvent[] = []

export function ChatMessages({
  messages,
  events = NO_EVENTS,
}: {
  messages: UIMessage[]
  events?: AgentActivityEvent[]
}) {
  const endRef = useRef<HTMLDivElement>(null)

  // Autoscroll on a new row, not on every re-render of the same ones. The
  // counts are the trigger; the body itself only reads the ref.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
    // oxlint-disable-next-line react/exhaustive-effect-dependencies
  }, [messages.length, events.length])

  const lastMessageId = messages.length
    ? messages[messages.length - 1].id
    : null

  // A single timeline of chat turns plus log events, sorted by time.
  // Logs are embedded concisely into the flow instead of a separate block.
  type Row =
    | { kind: "message"; at: number; key: string; message: UIMessage }
    | {
        kind: "activity"
        at: number
        key: string
        activity: AgentActivityEvent
      }
  const rows: Row[] = []
  for (const message of messages) {
    rows.push({
      kind: "message",
      at: messageTs(message),
      key: message.id,
      message,
    })
  }
  for (const activity of events) {
    rows.push({
      kind: "activity",
      at: Date.parse(activity.ts),
      key: `activity-${activity.id}`,
      activity,
    })
  }
  rows.sort((left, right) => left.at - right.at)

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto overscroll-contain p-4">
      {rows.map((row) =>
        row.kind === "message" ? (
          <MessageBubble
            key={row.key}
            message={row.message}
            isLast={row.message.id === lastMessageId}
          />
        ) : (
          <div key={row.key} className="border-l-2 border-border">
            <AgentActivityLine event={row.activity} />
          </div>
        )
      )}
      <div ref={endRef} />
    </div>
  )
}
