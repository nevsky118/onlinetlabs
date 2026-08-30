"use client"

import { sessionStateQuery } from "@/modules/session"
import { track } from "@repo/api/analytics"
import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import { Switch } from "@repo/design-system/ui/switch"
import { useRouter } from "@repo/i18n/navigation"
import { useQuery } from "@tanstack/react-query"
import {
  Minimize2Icon,
  PanelLeftCloseIcon,
  PanelLeftIcon,
  SparklesIcon,
  XIcon,
} from "lucide-react"
import { useFormatter, useTranslations } from "next-intl"
import { useCallback, useEffect, useRef, useState } from "react"
import type { SessionSummary } from "../types"
import type { UIMessage } from "@ai-sdk/react"
import { fetchChatHistory, fetchChatSessions } from "../api"
import { ChatSuggestions } from "../components/chat-empty-state"
import { ChatInput } from "../components/chat-input"
import { ChatMessages } from "../components/chat-messages"
import { ModelSelector } from "../components/model-selector"
import { useAgentActivity } from "../hooks/use-agent-activity"
import { useChatStream } from "../hooks/use-chat-stream"
import { useInterventions } from "../hooks/use-interventions"
import { getDomainLabel, mapToUIMessage } from "../lib/utils"
import { chatHistoryQuery, chatModelsQuery } from "../query"

type Archive = {
  sessionId: string
  labSlug: string
  date: string
}

// Fullscreen chat on its own URL, like CF /sphere. A framed window with a
// collapsible session history sidebar on the left
export function ChatView({
  sessionId,
  canViewLogs = false,
}: {
  sessionId: string
  canViewLogs?: boolean
}) {
  const t = useTranslations("dashboard.chat.chatView")
  const format = useFormatter()
  const router = useRouter()
  const { data: state } = useQuery(sessionStateQuery(sessionId))
  const labSlug = state?.lab.slug ?? ""

  const [archive, setArchive] = useState<Archive | null>(null)
  const [pastSessions, setPastSessions] = useState<SessionSummary[]>([])
  const [pastMessages, setPastMessages] = useState<UIMessage[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const historyFetchAbort = useRef<AbortController | null>(null)

  // Agent logs toggle, state kept in localStorage
  const [logsEnabled, setLogsEnabled] = useState<boolean>(
    () =>
      typeof window !== "undefined" &&
      localStorage.getItem(`agent-logs:${sessionId}`) === "true"
  )
  const onLogsToggle = useCallback(
    (checked: boolean) => {
      setLogsEnabled(checked)
      localStorage.setItem(`agent-logs:${sessionId}`, String(checked))
    },
    [sessionId]
  )

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

  // AI logs. Events stream while the toggle is on; they are embedded into the chat flow.
  const { events: activityEvents } = useAgentActivity(
    sessionId,
    canViewLogs && logsEnabled && !archive
  )

  const { data: history } = useQuery(chatHistoryQuery(sessionId))

  // The functional update does not wipe out interventions that could have
  // arrived before the history loaded
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
      .then((data) =>
        setPastSessions(data.filter((session) => session.id !== sessionId))
      )
      .catch(() => {})
    return () => historyFetchAbort.current?.abort()
  }, [sessionId])

  const trackedHandleSubmit = useCallback(
    (event?: React.FormEvent) => {
      const trimmed = input.trim()
      if (trimmed) {
        track("chat_message_sent", {
          session_id: sessionId,
          lab_slug: labSlug,
          message_length: trimmed.length,
        })
      }
      handleSubmit(event)
    },
    [input, sessionId, labSlug, handleSubmit]
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

  const openArchive = (session: SessionSummary) => {
    track("chat_history_viewed", { past_session_id: session.id })
    setArchive({
      sessionId: session.id,
      labSlug: session.labSlug,
      date: format.dateTime(new Date(session.startedAt), {
        dateStyle: "short",
      }),
    })
    setPastMessages([])
    historyFetchAbort.current?.abort()
    historyFetchAbort.current = new AbortController()
    fetchChatHistory(session.id, historyFetchAbort.current.signal)
      .then((data) => setPastMessages(data.map(mapToUIMessage)))
      .catch(() => {})
  }

  const { domain, name } = getDomainLabel(labSlug)
  const headerLabel = archive
    ? t("archiveHeader", { date: archive.date })
    : `${domain} / ${name}`

  return (
    <div className="fixed inset-0 z-50 flex bg-muted p-2">
      <div className="flex h-full w-full animate-in overflow-hidden border bg-background duration-300 fade-in-0 zoom-in-95">
        <div
          className={cn(
            "relative hidden shrink-0 overflow-hidden border-r transition-[width,border-color] duration-300 ease-in-out md:block",
            sidebarOpen ? "w-[280px]" : "w-0 border-r-transparent"
          )}
        >
          <div className="flex h-full w-[280px] flex-col">
            <div className="flex h-14 shrink-0 items-center gap-2 border-b pr-2 pl-4">
              <SparklesIcon className="size-4 text-muted-foreground" />
              <p className="text-sm font-medium whitespace-nowrap">
                {t("chat")}
              </p>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="ml-auto text-muted-foreground hover:text-foreground"
                aria-label={t("hideSidebar")}
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
                  "flex w-full cursor-pointer items-center gap-2 px-2 py-2 text-left text-sm hover:bg-muted",
                  !archive
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <span className="truncate">
                  {t("current", { domain, name })}
                </span>
              </button>
            </nav>
            <div className="min-h-0 flex-1 overflow-y-auto p-2 pt-0">
              <p className="px-2 py-1.5 text-xs text-muted-foreground">
                {t("history")}
              </p>
              {pastSessions.length === 0 ? (
                <p className="px-2 py-1 text-xs text-muted-foreground">
                  {t("noPastSessions")}
                </p>
              ) : (
                pastSessions.map((pastSession) => {
                  const { domain: pastDomain, name: pastName } = getDomainLabel(
                    pastSession.labSlug
                  )
                  return (
                    <button
                      key={pastSession.id}
                      type="button"
                      onClick={() => openArchive(pastSession)}
                      className={cn(
                        "flex w-full cursor-pointer flex-col gap-0.5 px-2 py-2 text-left hover:bg-muted",
                        archive?.sessionId === pastSession.id && "bg-muted"
                      )}
                    >
                      <span className="truncate text-sm text-foreground">
                        {pastDomain} / {pastName}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {format.dateTime(new Date(pastSession.startedAt), {
                          dateStyle: "short",
                        })}
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
                  aria-label={t("showSidebar")}
                  onClick={() => setSidebarOpen(true)}
                >
                  <PanelLeftIcon />
                </Button>
              )}
            </div>
            <p className="max-w-sm truncate text-center text-sm text-muted-foreground">
              {headerLabel}
            </p>
            <div className="flex items-center justify-end gap-2">
              {canViewLogs && !archive && (
                <div className="flex items-center gap-1.5">
                  <Switch
                    size="sm"
                    checked={logsEnabled}
                    onCheckedChange={onLogsToggle}
                    aria-label={t("aiLogs")}
                  />
                  <span className="text-xs text-muted-foreground">
                    {t("aiLogs")}
                  </span>
                </div>
              )}
              <Button
                type="button"
                variant="outline"
                size="icon"
                aria-label={t("collapseToPanel")}
                onClick={() => router.push(`/session/${sessionId}?chat=1`)}
              >
                <Minimize2Icon />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={t("closeChat")}
                onClick={() => router.push(`/session/${sessionId}`)}
              >
                <XIcon />
              </Button>
            </div>
          </header>

          {archive ? (
            <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col">
              <div className="flex items-center justify-between gap-2 border-b bg-card px-4 py-2">
                <span className="truncate text-xs text-muted-foreground">
                  {t("archiveDetail", {
                    domain: getDomainLabel(archive.labSlug).domain,
                    name: getDomainLabel(archive.labSlug).name,
                    date: archive.date,
                  })}
                </span>
                <Button
                  type="button"
                  variant="outline"
                  size="xs"
                  onClick={() => setArchive(null)}
                >
                  {t("backToCurrent")}
                </Button>
              </div>
              <ChatMessages messages={pastMessages} />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto px-6 py-9">
              <div className="flex w-full max-w-3xl flex-col items-center gap-6">
                <h1 className="text-center text-2xl font-semibold sm:text-4xl">
                  {t("greeting")}
                </h1>
                <ChatInput
                  input={input}
                  setInput={setInput}
                  handleSubmit={trackedHandleSubmit}
                  status={status}
                  stop={stop}
                  large
                  className="w-full p-0"
                  modelSelector={
                    modelsData ? (
                      <ModelSelector
                        models={modelsData.models}
                        canSelect={modelsData.canSelect}
                        value={
                          modelId || modelsData.defaultModelId || undefined
                        }
                        onValueChange={onModelChange}
                      />
                    ) : null
                  }
                />
                <ChatSuggestions horizontal onSuggestion={onSuggestion} />
              </div>
            </div>
          ) : (
            <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col">
              <ChatMessages messages={messages} events={activityEvents} />
              <ChatInput
                input={input}
                setInput={setInput}
                handleSubmit={trackedHandleSubmit}
                status={status}
                stop={stop}
                large
                modelSelector={
                  modelsData ? (
                    <ModelSelector
                      models={modelsData.models}
                      canSelect={modelsData.canSelect}
                      value={modelId || modelsData.defaultModelId || undefined}
                      onValueChange={onModelChange}
                    />
                  ) : null
                }
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
