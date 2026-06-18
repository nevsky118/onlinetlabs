"use client"

import type { UIMessage } from "@ai-sdk/react"
import { useQuery } from "@tanstack/react-query"
import {
  Minimize2Icon,
  PanelLeftCloseIcon,
  PanelLeftIcon,
  SparklesIcon,
  XIcon,
} from "lucide-react"
import { useRouter } from "next/navigation"
import { useCallback, useEffect, useRef, useState } from "react"
import type { SessionSummary } from "../types"
import { fetchChatHistory, fetchChatSessions } from "../api"
import { ChatSuggestions } from "../components/chat-empty-state"
import { ChatInput } from "../components/chat-input"
import { ChatMessages } from "../components/chat-messages"
import { ModelSelector } from "../components/model-selector"
import { useChatStream } from "../hooks/use-chat-stream"
import { useInterventions } from "../hooks/use-interventions"
import { getDomainLabel, mapToUIMessage } from "../lib/utils"
import { chatHistoryQuery, chatModelsQuery } from "../query"
import { track } from "@/lib/analytics"
import { cn } from "@/lib/utils"
import { sessionStateQuery } from "@/modules/session"
import { Button } from "@/ui/button"

type Archive = {
  sessionId: string
  labSlug: string
  date: string
}

// Полноэкранный чат на отдельном URL, как CF /sphere:
// окно в рамке, слева collapsible-сайдбар истории сессий
export function ChatView({ sessionId }: { sessionId: string }) {
  const router = useRouter()
  const { data: state } = useQuery(sessionStateQuery(sessionId))
  const labSlug = state?.lab.slug ?? ""

  const [archive, setArchive] = useState<Archive | null>(null)
  const [pastSessions, setPastSessions] = useState<SessionSummary[]>([])
  const [pastMessages, setPastMessages] = useState<UIMessage[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const historyFetchAbort = useRef<AbortController | null>(null)

  const [modelId, setModelId] = useState<string>(
    () =>
      (typeof window !== "undefined" &&
        localStorage.getItem(`chat-model:${sessionId}`)) ||
      ""
  )
  const onModelChange = useCallback(
    (id: string) => {
      setModelId(id)
      localStorage.setItem(`chat-model:${sessionId}`, id)
    },
    [sessionId]
  )

  const { data: modelsData } = useQuery(chatModelsQuery())

  const {
    messages,
    status,
    stop,
    setMessages,
    input,
    setInput,
    handleSubmit,
    sendText,
  } = useChatStream(sessionId, modelId)

  useInterventions(sessionId, setMessages)

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
    historyFetchAbort.current?.abort()
    historyFetchAbort.current = new AbortController()
    fetchChatSessions(historyFetchAbort.current.signal)
      .then((data) => setPastSessions(data.filter((s) => s.id !== sessionId)))
      .catch(() => {})
    return () => historyFetchAbort.current?.abort()
  }, [sessionId])

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

  const { domain, name } = getDomainLabel(labSlug)
  const headerLabel = archive
    ? `Архив · ${archive.date}`
    : `${domain} / ${name}`

  return (
    <div className="bg-muted fixed inset-0 z-50 flex p-2">
      <div className="bg-background animate-in fade-in-0 zoom-in-95 flex h-full w-full overflow-hidden border duration-300">
        <div
          className={cn(
            "relative hidden shrink-0 overflow-hidden border-r transition-[width,border-color] duration-300 ease-in-out md:block",
            sidebarOpen ? "w-[280px]" : "w-0 border-r-transparent"
          )}
        >
          <div className="flex h-full w-[280px] flex-col">
            <div className="flex h-14 shrink-0 items-center gap-2 border-b pr-2 pl-4">
              <SparklesIcon className="text-muted-foreground size-4" />
              <p className="text-sm font-medium whitespace-nowrap">Чат</p>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="text-muted-foreground hover:text-foreground ml-auto"
                aria-label="Скрыть список диалогов"
                onClick={() => setSidebarOpen(false)}
              >
                <PanelLeftCloseIcon />
              </Button>
            </div>
            <nav className="flex flex-col gap-0.5 p-2">
              <button
                type="button"
                onClick={() => setArchive(null)}
                className={cn(
                  "hover:bg-muted flex w-full cursor-pointer items-center gap-2 px-2 py-2 text-left text-sm",
                  !archive
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <span className="truncate">
                  Текущая · {domain} / {name}
                </span>
              </button>
            </nav>
            <div className="min-h-0 flex-1 overflow-y-auto p-2 pt-0">
              <p className="text-muted-foreground px-2 py-1.5 text-xs">
                История
              </p>
              {pastSessions.length === 0 ? (
                <p className="text-muted-foreground px-2 py-1 text-xs">
                  Пока нет прошлых сессий
                </p>
              ) : (
                pastSessions.map((s) => {
                  const { domain: d, name: n } = getDomainLabel(s.labSlug)
                  return (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => openArchive(s)}
                      className={cn(
                        "hover:bg-muted flex w-full cursor-pointer flex-col gap-0.5 px-2 py-2 text-left",
                        archive?.sessionId === s.id && "bg-muted"
                      )}
                    >
                      <span className="text-foreground truncate text-sm">
                        {d} / {n}
                      </span>
                      <span className="text-muted-foreground text-xs">
                        {new Date(s.startedAt).toLocaleDateString("ru-RU")}
                      </span>
                    </button>
                  )
                })
              )}
            </div>
          </div>
        </div>

        <div className="flex h-full min-w-0 flex-1 flex-col">
          <header className="grid shrink-0 grid-cols-[1fr_auto_1fr] items-center gap-2 p-3.5">
            <div className="flex items-center gap-2">
              {!sidebarOpen && (
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  className="hidden md:inline-flex"
                  aria-label="Показать список диалогов"
                  onClick={() => setSidebarOpen(true)}
                >
                  <PanelLeftIcon />
                </Button>
              )}
            </div>
            <p className="text-muted-foreground max-w-sm truncate text-center text-sm">
              {headerLabel}
            </p>
            <div className="flex items-center justify-end gap-2">
              {!archive && modelsData && (
                <ModelSelector
                  models={modelsData.models}
                  canSelect={modelsData.canSelect}
                  value={modelId || modelsData.defaultModelId || undefined}
                  onValueChange={onModelChange}
                />
              )}
              <Button
                type="button"
                variant="outline"
                size="icon"
                aria-label="Свернуть в панель"
                onClick={() => router.push(`/session/${sessionId}?chat=1`)}
              >
                <Minimize2Icon />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label="Закрыть чат"
                onClick={() => router.push(`/session/${sessionId}`)}
              >
                <XIcon />
              </Button>
            </div>
          </header>

          {archive ? (
            <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col">
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
            </div>
          ) : messages.length === 0 ? (
            <div className="flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto px-6 py-9">
              <div className="flex w-full max-w-3xl flex-col items-center gap-6">
                <h1 className="text-center text-2xl font-semibold sm:text-4xl">
                  Чем займёмся сегодня?
                </h1>
                <ChatInput
                  input={input}
                  setInput={setInput}
                  handleSubmit={trackedHandleSubmit}
                  status={status}
                  stop={stop}
                  large
                  className="w-full p-0"
                />
                <ChatSuggestions horizontal onSuggestion={onSuggestion} />
              </div>
            </div>
          ) : (
            <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col">
              <ChatMessages messages={messages} />
              <ChatInput
                input={input}
                setInput={setInput}
                handleSubmit={trackedHandleSubmit}
                status={status}
                stop={stop}
                large
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
