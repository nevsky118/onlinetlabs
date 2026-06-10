"use client"

import type { UIMessage } from "@ai-sdk/react"
import { CheckIcon, CopyIcon } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { ChatResponse } from "./chat-response"
import { Button } from "@/ui/button"

function messageText(m: UIMessage): string {
  return m.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("")
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

export function ChatMessages({ messages }: { messages: UIMessage[] }) {
  const endRef = useRef<HTMLDivElement>(null)

  // biome-ignore lint/correctness/useExhaustiveDependencies: автоскролл к низу при появлении новых сообщений
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto overscroll-contain p-4">
      {messages.map((m, i) => {
        const text = messageText(m)
        const isLast = i === messages.length - 1
        if (m.role === "user") {
          return (
            <article
              key={m.id}
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
            key={m.id}
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
      })}
      <div ref={endRef} />
    </div>
  )
}
