"use client"

import type { UIMessage } from "@ai-sdk/react"
import { useQuery } from "@tanstack/react-query"
import type { TimelineItem } from "../types"
import { sessionTimelineQuery } from "../query"
import { type AgentActivityEvent, Conversation } from "@/modules/chat"
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/ui/sheet"
import { Skeleton } from "@/ui/skeleton"

// Таймлайн от бэкенда → формат чата: реплики студента/тьютора как сообщения,
// проактивные интервенции — как встроенные события (та же лента, что в чате).
function toChatTimeline(items: TimelineItem[]): {
  messages: UIMessage[]
  events: AgentActivityEvent[]
} {
  const messages: UIMessage[] = []
  const events: AgentActivityEvent[] = []
  items.forEach((it, i) => {
    if (it.kind === "intervention") {
      events.push({
        id: `i-${i}`,
        sessionId: "",
        userId: "",
        ts: it.ts,
        source: "intervention",
        kind: "dispatched",
        agent: it.action,
        severity: it.severity ?? "info",
        summary: it.text ?? "",
        detail: {
          action: it.action,
          hint_level: it.hintLevel,
          struggle_type: it.struggleType,
        },
      })
    } else {
      messages.push({
        id: `m-${i}`,
        role: it.kind === "student" ? "user" : "assistant",
        parts: (it.parts ?? []) as UIMessage["parts"],
        metadata: { createdAt: it.ts },
      } as UIMessage)
    }
  })
  return { messages, events }
}

function SessionDialogueBody({
  userId,
  sessionId,
  labTitle,
}: {
  userId: string
  sessionId: string
  labTitle: string
}) {
  const { data, isLoading } = useQuery(sessionTimelineQuery(userId, sessionId))
  const { messages, events } = data
    ? toChatTimeline(data)
    : { messages: [], events: [] }

  // Кнопку закрытия рисует сам SheetContent — свою не добавляем (иначе два крестика).
  const header = (
    <div className="min-w-0">
      <div className="truncate text-sm font-medium">Диалог · {labTitle}</div>
      <div className="text-muted-foreground truncate text-xs">
        Чат студента с тьютором и проактивные подсказки
      </div>
    </div>
  )

  const emptyState = isLoading ? (
    <div className="flex flex-col gap-4 p-4">
      <Skeleton className="h-12 w-3/4" />
      <Skeleton className="h-12 w-2/3 self-end" />
    </div>
  ) : (
    <p className="text-muted-foreground p-4 text-sm">
      Диалога по этой сессии нет.
    </p>
  )

  return (
    <Conversation
      header={header}
      messages={messages}
      events={events}
      emptyState={emptyState}
    />
  )
}

export function SessionDialogueSheet({
  userId,
  session,
  children,
}: {
  userId: string
  session: { sessionId: string; labTitle: string }
  children: React.ReactNode
}) {
  return (
    <Sheet>
      <SheetTrigger asChild>{children}</SheetTrigger>
      <SheetContent className="flex w-full flex-col gap-0 p-0 sm:max-w-xl">
        <SheetTitle className="sr-only">Диалог · {session.labTitle}</SheetTitle>
        <SessionDialogueBody
          userId={userId}
          sessionId={session.sessionId}
          labTitle={session.labTitle}
        />
      </SheetContent>
    </Sheet>
  )
}
