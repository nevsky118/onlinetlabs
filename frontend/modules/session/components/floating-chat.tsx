"use client"

import type { UIMessage } from "@ai-sdk/react"
import {
  ArrowLeftIcon,
  HistoryIcon,
  MessageCircleIcon,
  XIcon,
} from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"
import { useChatStream } from "../hooks/use-chat-stream"
import { useInterventions } from "../hooks/use-interventions"
import { ChatInput } from "./chat-input"
import { ChatMessages } from "./chat-messages"
import { useIsMobile } from "@/hooks/use-mobile"
import { track } from "@/lib/analytics"
import { Button } from "@/ui/button"
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle } from "@/ui/drawer"

type ChatView =
  | { mode: "active" }
  | { mode: "history_list" }
  | {
      mode: "history_session"
      sessionId: string
      labSlug: string
      date: string
    }

interface SessionSummary {
  id: string
  lab_slug: string
  started_at: string
  status: string
}

function getDomainLabel(labSlug: string): { domain: string; name: string } {
  if (labSlug.includes("docker") || labSlug.includes("container")) {
    return { domain: "Docker", name: labSlug }
  }
  if (labSlug.includes("postgres") || labSlug.includes("sql")) {
    return { domain: "PostgreSQL", name: labSlug }
  }
  return { domain: "GNS3", name: labSlug }
}

function mapToUIMessage(m: {
  id: string
  role: string
  parts: unknown[]
}): UIMessage {
  return {
    id: m.id,
    role: m.role as "user" | "assistant",
    parts: m.parts as UIMessage["parts"],
  }
}

export function FloatingChat({
  sessionId,
  labSlug,
}: {
  sessionId: string
  labSlug: string
}) {
  const [open, setOpen] = useState(false)
  const [unread, setUnread] = useState(0)
  const [view, setView] = useState<ChatView>({ mode: "active" })
  const [pastSessions, setPastSessions] = useState<SessionSummary[]>([])
  const [pastMessages, setPastMessages] = useState<UIMessage[]>([])
  const historyLoadedRef = useRef(false)
  const historyFetchAbort = useRef<AbortController | null>(null)
  const isMobile = useIsMobile()

  const { messages, status, stop, setMessages, input, setInput, handleSubmit } =
    useChatStream(sessionId)

  const onUnread = useCallback(() => {
    if (!open) setUnread((n) => n + 1)
  }, [open])

  useInterventions(sessionId, setMessages, onUnread)

  // Грузим историю чата этой сессии при монтировании.
  // Функциональный апдейт не затирает интервенции, которые могли прийти
  // раньше, чем загрузилась история
  useEffect(() => {
    if (historyLoadedRef.current) return
    historyLoadedRef.current = true
    fetch(`/api/chat/history/${sessionId}`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data: { id: string; role: string; parts: unknown[] }[]) => {
        if (data.length > 0) {
          setMessages((prev) =>
            prev.length === 0 ? data.map(mapToUIMessage) : prev
          )
        }
      })
      .catch(() => {})
  }, [sessionId, setMessages])

  const onOpen = () => {
    setOpen(true)
    setUnread(0)
    track("chat_opened", { session_id: sessionId, lab_slug: labSlug })
  }

  // input меняется на каждый ввод символа, держим его в ref,
  // чтобы trackedHandleSubmit оставался стабильным
  const inputRef = useRef(input)
  inputRef.current = input

  const trackedHandleSubmit = useCallback(
    (e?: React.FormEvent) => {
      if (inputRef.current.trim()) {
        track("chat_message_sent", {
          session_id: sessionId,
          lab_slug: labSlug,
          message_length: inputRef.current.trim().length,
        })
      }
      handleSubmit(e)
    },
    [sessionId, labSlug, handleSubmit]
  )

  // Фиксируем ответ когда статус переходит из streaming в ready
  const prevStatusRef = useRef(status)
  useEffect(() => {
    if (prevStatusRef.current === "streaming" && status === "ready") {
      track("chat_response_received", {
        session_id: sessionId,
        lab_slug: labSlug,
      })
    }
    prevStatusRef.current = status
  }, [status, sessionId, labSlug])

  useEffect(() => {
    return () => {
      historyFetchAbort.current?.abort()
    }
  }, [])

  const openHistoryList = () => {
    historyFetchAbort.current?.abort()
    historyFetchAbort.current = new AbortController()
    setView({ mode: "history_list" })
    fetch("/api/chat/sessions", { signal: historyFetchAbort.current.signal })
      .then((r) => (r.ok ? r.json() : []))
      .then((data: SessionSummary[]) => {
        setPastSessions(data.filter((s) => s.id !== sessionId))
      })
      .catch((e: unknown) => {
        if (e instanceof Error && e.name !== "AbortError") {
          // сетевые ошибки тихо игнорируем
        }
      })
  }

  const openHistorySession = (s: SessionSummary) => {
    track("chat_history_viewed", { past_session_id: s.id })
    setView({
      mode: "history_session",
      sessionId: s.id,
      labSlug: s.lab_slug,
      date: new Date(s.started_at).toLocaleDateString("ru-RU"),
    })
    historyFetchAbort.current?.abort()
    historyFetchAbort.current = new AbortController()
    fetch(`/api/chat/history/${s.id}`, {
      signal: historyFetchAbort.current.signal,
    })
      .then((r) => (r.ok ? r.json() : []))
      .then((data: { id: string; role: string; parts: unknown[] }[]) => {
        setPastMessages(data.map(mapToUIMessage))
      })
      .catch((e: unknown) => {
        if (e instanceof Error && e.name !== "AbortError") {
          // тихо игнорируем
        }
      })
  }

  const { domain, name } = getDomainLabel(labSlug)

  function renderHeader(onClose: () => void) {
    return (
      <div className="flex items-center justify-between border-b px-4 py-3">
        {view.mode !== "active" ? (
          <button
            type="button"
            onClick={() => setView({ mode: "active" })}
            className="text-muted-foreground hover:text-foreground flex items-center gap-1.5 text-sm"
          >
            <ArrowLeftIcon />
            Назад
          </button>
        ) : (
          <span className="text-foreground font-mono text-xs tracking-wide">
            TutorAgent
            <span className="text-muted-foreground">
              {" "}
              · {domain} / {name}
            </span>
          </span>
        )}
        <div className="flex items-center gap-1">
          {view.mode === "active" && (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              className="rounded-none"
              onClick={openHistoryList}
              aria-label="История чатов"
            >
              <HistoryIcon />
            </Button>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="rounded-none"
            onClick={onClose}
            aria-label="Свернуть чат"
          >
            <XIcon />
          </Button>
        </div>
      </div>
    )
  }

  function renderBody() {
    if (view.mode === "history_list") {
      return (
        <div className="flex flex-1 flex-col overflow-y-auto p-2">
          {pastSessions.length === 0 ? (
            <p className="text-muted-foreground p-4 text-center text-xs">
              Нет прошлых сессий
            </p>
          ) : (
            pastSessions.map((s) => {
              const { domain: d, name: n } = getDomainLabel(s.lab_slug)
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => openHistorySession(s)}
                  className="hover:bg-accent flex flex-col gap-0.5 px-3 py-2.5 text-left"
                >
                  <span className="text-foreground text-xs font-medium">
                    {d} / {n}
                  </span>
                  <span className="text-muted-foreground text-[10px]">
                    {new Date(s.started_at).toLocaleDateString("ru-RU")}
                  </span>
                </button>
              )
            })
          )}
        </div>
      )
    }
    if (view.mode === "history_session") {
      return (
        <div className="flex flex-1 flex-col overflow-hidden">
          <ChatMessages messages={pastMessages} />
        </div>
      )
    }
    // активный режим
    return (
      <div className="flex flex-1 flex-col overflow-hidden">
        <ChatMessages messages={messages} />
        <ChatInput
          input={input}
          setInput={setInput}
          handleSubmit={trackedHandleSubmit}
          status={status}
          stop={stop}
        />
      </div>
    )
  }

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={onOpen}
          aria-label="Открыть чат тьютора"
          className="bg-card text-card-foreground hover:bg-accent fixed right-4 bottom-20 z-40 inline-flex size-12 items-center justify-center border shadow-lg md:right-6 md:bottom-6"
        >
          <MessageCircleIcon className="size-5" />
          {unread > 0 && (
            <span className="bg-destructive text-destructive-foreground absolute -top-1 -right-1 flex size-5 items-center justify-center text-[10px] font-semibold">
              {unread}
            </span>
          )}
        </button>
      )}

      {open && !isMobile && (
        <div className="bg-card text-card-foreground fixed right-6 bottom-6 z-50 flex h-[32rem] w-96 flex-col overflow-hidden border shadow-xl">
          {renderHeader(() => setOpen(false))}
          {renderBody()}
        </div>
      )}

      {isMobile && (
        <Drawer open={open} onOpenChange={setOpen}>
          <DrawerContent>
            <DrawerHeader className="border-b py-0">
              {view.mode !== "active" ? (
                <div className="flex items-center justify-between px-4 py-3">
                  <button
                    type="button"
                    onClick={() => setView({ mode: "active" })}
                    className="text-muted-foreground hover:text-foreground flex items-center gap-1.5 text-sm"
                  >
                    <ArrowLeftIcon />
                    Назад
                  </button>
                  <DrawerTitle className="sr-only">История чата</DrawerTitle>
                </div>
              ) : (
                <div className="flex items-center justify-between px-4 py-3">
                  <DrawerTitle className="font-mono text-xs tracking-wide">
                    TutorAgent
                    <span className="text-muted-foreground font-normal">
                      {" "}
                      · {domain} / {name}
                    </span>
                  </DrawerTitle>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    className="rounded-none"
                    onClick={openHistoryList}
                    aria-label="История чатов"
                  >
                    <HistoryIcon />
                  </Button>
                </div>
              )}
            </DrawerHeader>
            <div className="flex h-[60vh] flex-col">{renderBody()}</div>
          </DrawerContent>
        </Drawer>
      )}
    </>
  )
}
