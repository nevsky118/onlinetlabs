"use client"

import type { UIMessage } from "@ai-sdk/react"
import { useQuery } from "@tanstack/react-query"
import { CheckIcon, ChevronDownIcon, Maximize2Icon, XIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useCallback, useEffect, useRef, useState } from "react"
import type { SessionSummary } from "../types"
import { fetchChatHistory, fetchChatSessions } from "../api"
import { useChatStream } from "../hooks/use-chat-stream"
import { useInterventions } from "../hooks/use-interventions"
import { getDomainLabel, mapToUIMessage } from "../lib/utils"
import { chatHistoryQuery } from "../query"
import { ChatEmptyState } from "./chat-empty-state"
import { ChatInput } from "./chat-input"
import { ChatMessages } from "./chat-messages"
import { CHAT_PANEL_MIN_WIDTH, useChatPanel } from "./chat-panel-provider"
import { useIsMobile } from "@/hooks/use-mobile"
import { track } from "@/lib/analytics"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/ui/dropdown-menu"

type Archive = {
  sessionId: string
  labSlug: string
  date: string
}

export function ChatPanel({
  sessionId,
  labSlug,
}: {
  sessionId: string
  labSlug: string
}) {
  const router = useRouter()
  const {
    open,
    closePanel,
    width,
    setWidth,
    resizing,
    setResizing,
    bumpUnread,
  } = useChatPanel()
  const isMobile = useIsMobile()

  const [archive, setArchive] = useState<Archive | null>(null)
  const [pastSessions, setPastSessions] = useState<SessionSummary[]>([])
  const [pastMessages, setPastMessages] = useState<UIMessage[]>([])
  const historyFetchAbort = useRef<AbortController | null>(null)
  const spotlightRef = useRef<HTMLDivElement>(null)

  const {
    messages,
    status,
    stop,
    setMessages,
    input,
    setInput,
    handleSubmit,
    sendText,
  } = useChatStream(sessionId)

  const openRef = useRef(open)
  openRef.current = open
  const onUnread = useCallback(() => {
    if (!openRef.current) bumpUnread()
  }, [bumpUnread])

  useInterventions(sessionId, setMessages, onUnread)

  // Грузим историю чата этой сессии.
  const { data: history } = useQuery(chatHistoryQuery(sessionId))

  // Функциональный апдейт не затирает интервенции, которые могли прийти
  // раньше, чем загрузилась история
  useEffect(() => {
    if (!history || history.length === 0) return
    setMessages((prev) =>
      prev.length === 0 ? history.map(mapToUIMessage) : prev
    )
  }, [history, setMessages])

  useEffect(() => {
    if (open) track("chat_opened", { session_id: sessionId, lab_slug: labSlug })
  }, [open, sessionId, labSlug])

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

  const onSuggestion = useCallback(
    (prompt: string) => {
      track("chat_message_sent", {
        session_id: sessionId,
        lab_slug: labSlug,
        message_length: prompt.length,
      })
      sendText(prompt)
    },
    [sessionId, labSlug, sendText]
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
    return () => historyFetchAbort.current?.abort()
  }, [])

  const loadSessions = () => {
    historyFetchAbort.current?.abort()
    historyFetchAbort.current = new AbortController()
    fetchChatSessions(historyFetchAbort.current.signal)
      .then((data) => setPastSessions(data.filter((s) => s.id !== sessionId)))
      .catch(() => {})
  }

  const openArchive = (s: SessionSummary) => {
    track("chat_history_viewed", { past_session_id: s.id })
    setArchive({
      sessionId: s.id,
      labSlug: s.labSlug,
      date: new Date(s.startedAt).toLocaleDateString("ru-RU"),
    })
    setPastMessages([])
    historyFetchAbort.current?.abort()
    historyFetchAbort.current = new AbortController()
    fetchChatHistory(s.id, historyFetchAbort.current.signal)
      .then((data) => setPastMessages(data.map(mapToUIMessage)))
      .catch(() => {})
  }

  // Ресайз левой кромкой, как в Cloudflare: на время drag отключаем transition
  const onResizeStart = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isMobile) return
    e.preventDefault()
    setResizing(true)
    const onMove = (ev: PointerEvent) => {
      const max = Math.max(CHAT_PANEL_MIN_WIDTH, window.innerWidth - 160)
      setWidth(
        Math.min(
          max,
          Math.max(CHAT_PANEL_MIN_WIDTH, window.innerWidth - ev.clientX)
        )
      )
    }
    const onUp = () => {
      setResizing(false)
      window.removeEventListener("pointermove", onMove)
      window.removeEventListener("pointerup", onUp)
    }
    window.addEventListener("pointermove", onMove)
    window.addEventListener("pointerup", onUp)
  }

  // Точечная сетка с подсветкой под курсором (CF spotlight)
  const onSpotlightMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = spotlightRef.current
    if (!el) return
    const r = e.currentTarget.getBoundingClientRect()
    el.style.setProperty("--spot-x", `${e.clientX - r.x}px`)
    el.style.setProperty("--spot-y", `${e.clientY - r.y}px`)
    el.style.opacity = "1"
  }

  const { domain, name } = getDomainLabel(labSlug)
  const headerLabel = archive
    ? `Архив · ${archive.date}`
    : `${domain} / ${name}`

  return (
    <aside
      inert={!open}
      aria-label="Чат с ИИ-тьютором"
      className={cn(
        "bg-background fixed inset-y-0 right-0 z-50 flex flex-col border-l",
        !resizing && "transition-[transform,width] duration-300 ease-in-out",
        isMobile && "w-full"
      )}
      style={{
        width: isMobile ? undefined : width,
        transform: open ? "translateX(0)" : "translateX(100%)",
      }}
    >
      {!isMobile && (
        <div
          role="separator"
          tabIndex={0}
          aria-orientation="vertical"
          aria-label="Изменить ширину панели"
          aria-valuenow={width}
          aria-valuemin={CHAT_PANEL_MIN_WIDTH}
          onPointerDown={onResizeStart}
          onKeyDown={(e) => {
            if (e.key === "ArrowLeft") setWidth(width + 24)
            if (e.key === "ArrowRight")
              setWidth(Math.max(CHAT_PANEL_MIN_WIDTH, width - 24))
          }}
          className="hover:bg-border focus-visible:bg-border absolute inset-y-0 left-0 z-20 w-1 cursor-col-resize outline-none transition-colors"
        />
      )}

      <div
        className={cn(
          "flex min-h-0 flex-1 flex-col transition-opacity duration-200",
          open ? "opacity-100" : "opacity-0"
        )}
      >
        {/* Хедер */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b px-4">
          <DropdownMenu
            onOpenChange={(o) => {
              if (o) loadSessions()
            }}
          >
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                className="-ml-2 max-w-[200px] justify-between gap-2"
              >
                <span className="truncate">{headerLabel}</span>
                <ChevronDownIcon className="text-muted-foreground size-3 shrink-0" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-64">
              <DropdownMenuLabel>История сессий</DropdownMenuLabel>
              <DropdownMenuGroup>
                <DropdownMenuItem onSelect={() => setArchive(null)}>
                  <span className="truncate">
                    Текущая · {domain} / {name}
                  </span>
                  {!archive && <CheckIcon className="ml-auto" />}
                </DropdownMenuItem>
                {pastSessions.map((s) => {
                  const { domain: d, name: n } = getDomainLabel(s.labSlug)
                  return (
                    <DropdownMenuItem
                      key={s.id}
                      onSelect={() => openArchive(s)}
                    >
                      <span className="truncate">
                        {d} / {n}
                      </span>
                      <span className="text-muted-foreground ml-auto text-xs">
                        {new Date(s.startedAt).toLocaleDateString("ru-RU")}
                      </span>
                    </DropdownMenuItem>
                  )
                })}
              </DropdownMenuGroup>
              {pastSessions.length === 0 && (
                <>
                  <DropdownMenuSeparator />
                  <p className="text-muted-foreground p-2 text-xs">
                    Пока нет прошлых сессий
                  </p>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="flex items-center gap-0.5">
            {!isMobile && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label="Открыть на всю страницу"
                onClick={() => router.push(`/session/${sessionId}/chat`)}
              >
                <Maximize2Icon />
              </Button>
            )}
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label="Закрыть чат"
              onClick={closePanel}
            >
              <XIcon />
            </Button>
          </div>
        </header>

        {/* Тело: точечная сетка + spotlight как в CF */}
        {/* biome-ignore lint/a11y/noStaticElementInteractions: mousemove чисто декоративный (подсветка точек) */}
        <div
          className="relative flex min-h-0 flex-1 flex-col"
          onMouseMove={onSpotlightMove}
          onMouseLeave={() => {
            if (spotlightRef.current) spotlightRef.current.style.opacity = "0"
          }}
        >
          <div className="pointer-events-none absolute inset-0 -z-10">
            <div
              className="absolute inset-0"
              style={{
                backgroundImage:
                  "radial-gradient(circle, color-mix(in oklab, var(--color-foreground) 8%, transparent) 1px, transparent 1px)",
                backgroundSize: "12px 12px",
              }}
            />
            <div
              ref={spotlightRef}
              className="absolute inset-0 opacity-0 transition-opacity duration-200"
              style={{
                background:
                  "radial-gradient(80px at var(--spot-x, -1000px) var(--spot-y, -1000px), color-mix(in oklab, var(--color-primary) 50%, transparent), transparent)",
                maskImage:
                  "radial-gradient(circle, black 1px, transparent 1px)",
                maskSize: "12px 12px",
              }}
            />
          </div>

          {archive ? (
            <>
              <div className="bg-card flex items-center justify-between gap-2 border-b px-4 py-2">
                <span className="text-muted-foreground truncate text-xs">
                  Архив · {getDomainLabel(archive.labSlug).domain} /{" "}
                  {getDomainLabel(archive.labSlug).name} · {archive.date}
                </span>
                <Button
                  type="button"
                  variant="outline"
                  size="xs"
                  onClick={() => setArchive(null)}
                >
                  К текущей
                </Button>
              </div>
              <ChatMessages messages={pastMessages} />
            </>
          ) : messages.length === 0 ? (
            <>
              <ChatEmptyState onSuggestion={onSuggestion} />
              <ChatInput
                input={input}
                setInput={setInput}
                handleSubmit={trackedHandleSubmit}
                status={status}
                stop={stop}
              />
            </>
          ) : (
            <>
              <ChatMessages messages={messages} />
              <ChatInput
                input={input}
                setInput={setInput}
                handleSubmit={trackedHandleSubmit}
                status={status}
                stop={stop}
              />
            </>
          )}
        </div>
      </div>
    </aside>
  )
}
