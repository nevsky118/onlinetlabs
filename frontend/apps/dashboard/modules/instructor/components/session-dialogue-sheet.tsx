"use client"

import { type AgentActivityEvent, Conversation } from "@/modules/chat"
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@repo/design-system/ui/sheet"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import type { TimelineItem } from "../types"
import type { UIMessage } from "@ai-sdk/react"
import { sessionTimelineQuery } from "../query"

// Backend timeline → chat format. Student/tutor turns become messages,
// proactive interventions become inline events (the same feed as in the chat).
function toChatTimeline(items: TimelineItem[]): {
  messages: UIMessage[]
  events: AgentActivityEvent[]
} {
  const messages: UIMessage[] = []
  const events: AgentActivityEvent[] = []
  items.forEach((it, index) => {
    if (it.kind === "intervention") {
      events.push({
        id: `i-${index}`,
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
        id: `m-${index}`,
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
  const t = useTranslations("dashboard.instructor.sessionDialogueSheet")
  const { data, isLoading } = useQuery(sessionTimelineQuery(userId, sessionId))
  const { messages, events } = data
    ? toChatTimeline(data)
    : { messages: [], events: [] }

  // SheetContent renders the close button itself, so we do not add our own (otherwise there are two crosses).
  const header = (
    <div className="min-w-0">
      <div className="truncate text-sm font-medium">
        {t("dialogueTitle", { labTitle })}
      </div>
      <div className="truncate text-xs text-muted-foreground">
        {t("dialogueSubtitle")}
      </div>
    </div>
  )

  const emptyState = isLoading ? (
    <div className="flex flex-col gap-4 p-4">
      <Skeleton className="h-12 w-3/4" />
      <Skeleton className="h-12 w-2/3 self-end" />
    </div>
  ) : (
    <p className="p-4 text-sm text-muted-foreground">{t("noDialogue")}</p>
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
  children: React.ReactElement
}) {
  const t = useTranslations("dashboard.instructor.sessionDialogueSheet")
  return (
    <Sheet>
      <SheetTrigger render={children} />
      <SheetContent className="flex w-full flex-col gap-0 p-0 sm:max-w-xl">
        <SheetTitle className="sr-only">
          {t("dialogueTitle", { labTitle: session.labTitle })}
        </SheetTitle>
        <SessionDialogueBody
          userId={userId}
          sessionId={session.sessionId}
          labTitle={session.labTitle}
        />
      </SheetContent>
    </Sheet>
  )
}
