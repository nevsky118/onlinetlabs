"use client"

import { track } from "@repo/api/analytics"
import { useIsMobile } from "@repo/design-system/hooks/use-mobile"
import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@repo/design-system/ui/dropdown-menu"
import { Switch } from "@repo/design-system/ui/switch"
import { useRouter } from "@repo/i18n/navigation"
import { useQuery } from "@tanstack/react-query"
import { CheckIcon, ChevronDownIcon, Maximize2Icon, XIcon } from "lucide-react"
import { useFormatter, useTranslations } from "next-intl"
import { useCallback, useEffect, useRef, useState } from "react"
import type { SessionSummary } from "../types"
import type { UIMessage } from "@ai-sdk/react"
import { fetchChatHistory, fetchChatSessions } from "../api"
import { useAgentActivity } from "../hooks/use-agent-activity"
import { useChatStream } from "../hooks/use-chat-stream"
import { useInterventions } from "../hooks/use-interventions"
import { getDomainLabel, mapToUIMessage } from "../lib/utils"
import { chatHistoryQuery, chatModelsQuery } from "../query"
import { ChatEmptyState } from "./chat-empty-state"
import { ChatInput } from "./chat-input"
import { ChatMessages } from "./chat-messages"
import { CHAT_PANEL_MIN_WIDTH, useChatPanel } from "./chat-panel-provider"
import { ModelSelector } from "./model-selector"

type Archive = {
  sessionId: string
  labSlug: string
  date: string
}

// No props. The session config comes from ChatProvider through context.
export function ChatPanel() {
  const t = useTranslations("dashboard.chat.chatPanel")
  const format = useFormatter()
  const router = useRouter()
  const {
    config: { sessionId, labSlug, canViewLogs },
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

  useInterventions(sessionId, setMessages, () => {
    if (!open) bumpUnread()
  })

  // AI logs. Events stream only while the toggle is on; they are embedded into the chat flow.
  const { events: activityEvents } = useAgentActivity(
    sessionId,
    canViewLogs && logsEnabled && !archive
  )

  // Load the chat history of this session.
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
    if (open) track("chat_opened", { session_id: sessionId, lab_slug: labSlug })
  }, [open, sessionId, labSlug])

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

  // Record the response when the status goes from streaming to ready
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
      .then((data) =>
        setPastSessions(data.filter((session) => session.id !== sessionId))
      )
      .catch(() => {})
  }

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

  // Resize by the left edge, like in Cloudflare. Transition is disabled while dragging
  const onResizeStart = (event: React.PointerEvent<HTMLDivElement>) => {
    if (isMobile) return
    event.preventDefault()
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

  // Dot grid with a highlight under the cursor (CF spotlight)
  const onSpotlightMove = (event: React.MouseEvent<HTMLDivElement>) => {
    const el = spotlightRef.current
    if (!el) return
    const bounds = event.currentTarget.getBoundingClientRect()
    el.style.setProperty("--spot-x", `${event.clientX - bounds.x}px`)
    el.style.setProperty("--spot-y", `${event.clientY - bounds.y}px`)
    el.style.opacity = "1"
  }

  const { domain, name } = getDomainLabel(labSlug)
  const headerLabel = archive
    ? t("archiveHeader", { date: archive.date })
    : `${domain} / ${name}`

  return (
    <aside
      inert={!open}
      aria-label={t("ariaLabel")}
      className={cn(
        "fixed inset-y-0 right-0 z-50 flex flex-col border-l bg-background",
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
          aria-label={t("resizeAriaLabel")}
          aria-valuenow={width}
          aria-valuemin={CHAT_PANEL_MIN_WIDTH}
          onPointerDown={onResizeStart}
          onKeyDown={(event) => {
            if (event.key === "ArrowLeft") setWidth(width + 24)
            if (event.key === "ArrowRight")
              setWidth(Math.max(CHAT_PANEL_MIN_WIDTH, width - 24))
          }}
          className="absolute inset-y-0 left-0 z-20 w-1 cursor-col-resize transition-colors outline-none hover:bg-border focus-visible:bg-border"
        />
      )}

      <div
        className={cn(
          "flex min-h-0 flex-1 flex-col transition-opacity duration-200",
          open ? "opacity-100" : "opacity-0"
        )}
      >
        {/* Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b px-4">
          <DropdownMenu
            onOpenChange={(isOpen) => {
              if (isOpen) loadSessions()
            }}
          >
            <DropdownMenuTrigger
              render={
                <Button
                  type="button"
                  variant="ghost"
                  className="-ml-2 max-w-[200px] justify-between gap-2"
                />
              }
            >
              <span className="truncate">{headerLabel}</span>
              <ChevronDownIcon className="size-3 shrink-0 text-muted-foreground" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-64">
              {/* base-ui throws when a label has no group ancestor. */}
              <DropdownMenuGroup>
                <DropdownMenuLabel>{t("sessionHistory")}</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => setArchive(null)}>
                  <span className="truncate">
                    {t("current", { domain, name })}
                  </span>
                  {!archive && <CheckIcon className="ml-auto" />}
                </DropdownMenuItem>
                {pastSessions.map((pastSession) => {
                  const { domain: pastDomain, name: pastName } = getDomainLabel(
                    pastSession.labSlug
                  )
                  return (
                    <DropdownMenuItem
                      key={pastSession.id}
                      onClick={() => openArchive(pastSession)}
                    >
                      <span className="truncate">
                        {pastDomain} / {pastName}
                      </span>
                      <span className="ml-auto text-xs text-muted-foreground">
                        {format.dateTime(new Date(pastSession.startedAt), {
                          dateStyle: "short",
                        })}
                      </span>
                    </DropdownMenuItem>
                  )
                })}
              </DropdownMenuGroup>
              {pastSessions.length === 0 && (
                <>
                  <DropdownMenuSeparator />
                  <p className="p-2 text-xs text-muted-foreground">
                    {t("noPastSessions")}
                  </p>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="flex items-center gap-1.5">
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
            {!isMobile && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label={t("openFullPage")}
                onClick={() => router.push(`/session/${sessionId}/chat`)}
              >
                <Maximize2Icon />
              </Button>
            )}
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label={t("closeChat")}
              onClick={closePanel}
            >
              <XIcon />
            </Button>
          </div>
        </header>

        {/* Body. Dot grid + spotlight like in CF */}
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
            </>
          ) : (
            <>
              <ChatMessages messages={messages} events={activityEvents} />
              <ChatInput
                input={input}
                setInput={setInput}
                handleSubmit={trackedHandleSubmit}
                status={status}
                stop={stop}
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
            </>
          )}
        </div>
      </div>
    </aside>
  )
}
