"use client"

import type { UIMessage } from "@ai-sdk/react"
import { CheckIcon, CopyIcon } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import type { AgentActivityEvent } from "../types"
import { AgentActivityLine } from "./agent-activity-console"
import { ChatResponse } from "./chat-response"
import { Button } from "@/ui/button"

function messageText(m: UIMessage): string {
  return m.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("")
}

// Время сообщения: история несёт createdAt в metadata; у live-сообщений его нет —
// им проставляем момент первого появления (нужно для встраивания логов по времени).
function messageTs(m: UIMessage, seen: Map<string, number>): number {
  const meta = m.metadata as { createdAt?: string } | undefined
  if (meta?.createdAt) return Date.parse(meta.createdAt)
  let t = seen.get(m.id)
  if (t === undefined) {
    t = Date.now()
    seen.set(m.id, t)
  }
  return t
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-xs"
      aria-label="Скопировать ответ"
      className="text-muted-foreground hover:text-foreground"
      onClick={() => {
        navigator.clipboard.writeText(text).then(() => {
          setCopied(true)
          setTimeout(() => setCopied(false), 1500)
        })
      }}
    >
      {copied ? <CheckIcon /> : <CopyIcon />}
    </Button>
  )
}

function MessageBubble({ m, isLast }: { m: UIMessage; isLast: boolean }) {
  const text = messageText(m)
  if (m.role === "user") {
    return (
      <article
        data-sender="user"
        className="animate-in fade-in-0 flex flex-col items-end duration-300"
      >
        <div className="bg-muted text-foreground ml-auto w-fit max-w-[85%] px-4 py-3 text-sm leading-relaxed break-words whitespace-pre-wrap">
          {text}
        </div>
      </article>
    )
  }
  return (
    <article
      data-sender="ai"
      className="group/message animate-in fade-in-0 flex flex-col items-start gap-1 duration-300"
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

export function ChatMessages({
  messages,
  events = [],
}: {
  messages: UIMessage[]
  events?: AgentActivityEvent[]
}) {
  const endRef = useRef<HTMLDivElement>(null)
  const seenRef = useRef<Map<string, number>>(new Map())

  // biome-ignore lint/correctness/useExhaustiveDependencies: автоскролл при новых сообщениях/событиях
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, events])

  const lastMessageId = messages.length
    ? messages[messages.length - 1].id
    : null

  // Единый таймлайн: реплики чата + события логов, отсортированные по времени.
  // Логи лаконично встроены в поток, а не отдельным блоком.
  type Row =
    | { kind: "msg"; t: number; key: string; m: UIMessage }
    | { kind: "evt"; t: number; key: string; e: AgentActivityEvent }
  const rows: Row[] = []
  for (const m of messages) {
    rows.push({ kind: "msg", t: messageTs(m, seenRef.current), key: m.id, m })
  }
  for (const e of events) {
    rows.push({ kind: "evt", t: Date.parse(e.ts), key: `evt-${e.id}`, e })
  }
  rows.sort((a, b) => a.t - b.t)

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto overscroll-contain p-4">
      {rows.map((row) =>
        row.kind === "msg" ? (
          <MessageBubble
            key={row.key}
            m={row.m}
            isLast={row.m.id === lastMessageId}
          />
        ) : (
          <div key={row.key} className="border-border border-l-2">
            <AgentActivityLine event={row.e} />
          </div>
        )
      )}
      <div ref={endRef} />
    </div>
  )
}
