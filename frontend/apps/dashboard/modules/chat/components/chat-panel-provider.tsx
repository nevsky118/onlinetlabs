"use client"

import { useIsMobile } from "@repo/design-system/hooks/use-mobile"
import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import { SparklesIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { createContext, use, useCallback, useMemo, useState } from "react"

export const CHAT_PANEL_DEFAULT_WIDTH = 450
export const CHAT_PANEL_MIN_WIDTH = 360

// The session config is the only set of props the page passes to the chat.
// From there the panel/trigger take it from context, without prop-drilling.
export type ChatConfig = {
  sessionId: string
  labSlug: string
  canViewLogs: boolean
}

type ChatPanelContextValue = {
  config: ChatConfig
  open: boolean
  openPanel: () => void
  closePanel: () => void
  width: number
  setWidth: (w: number) => void
  resizing: boolean
  setResizing: (v: boolean) => void
  unread: number
  bumpUnread: () => void
}

const ChatPanelContext = createContext<ChatPanelContextValue | null>(null)

export function useChatPanel() {
  const ctx = use(ChatPanelContext)
  if (!ctx) throw new Error("useChatPanel used outside ChatProvider")
  return ctx
}

export function ChatProvider({
  children,
  sessionId,
  labSlug,
  canViewLogs = false,
  defaultOpen = false,
}: {
  children: React.ReactNode
  sessionId: string
  labSlug: string
  canViewLogs?: boolean
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  const [width, setWidth] = useState(CHAT_PANEL_DEFAULT_WIDTH)
  const [resizing, setResizing] = useState(false)
  const [unread, setUnread] = useState(0)

  const openPanel = useCallback(() => {
    setOpen(true)
    setUnread(0)
  }, [])
  const closePanel = useCallback(() => setOpen(false), [])
  const bumpUnread = useCallback(() => setUnread((n) => n + 1), [])

  const config = useMemo<ChatConfig>(
    () => ({ sessionId, labSlug, canViewLogs }),
    [sessionId, labSlug, canViewLogs]
  )

  const value = useMemo(
    () => ({
      config,
      open,
      openPanel,
      closePanel,
      width,
      setWidth,
      resizing,
      setResizing,
      unread,
      bumpUnread,
    }),
    [config, open, openPanel, closePanel, width, resizing, unread, bumpUnread]
  )

  return <ChatPanelContext value={value}>{children}</ChatPanelContext>
}

// Shifts the content left when the panel is open, like in the Cloudflare dash
export function ChatInset({ children }: { children: React.ReactNode }) {
  const { open, width, resizing } = useChatPanel()
  const isMobile = useIsMobile()

  return (
    <div
      className={cn(
        "min-w-0",
        !resizing && "transition-[margin-right] duration-300 ease-in-out"
      )}
      style={{ marginRight: !open || isMobile ? 0 : `${width}px` }}
    >
      {children}
    </div>
  )
}

export function ChatTrigger({ onOpen }: { onOpen?: () => void }) {
  const t = useTranslations("dashboard.chat.trigger")
  const { open, openPanel, closePanel, unread } = useChatPanel()

  return (
    <Button
      type="button"
      variant="ghost"
      className="relative"
      onClick={() => {
        if (open) {
          closePanel()
          return
        }
        openPanel()
        onOpen?.()
      }}
    >
      <SparklesIcon
        data-icon="inline-start"
        className="text-muted-foreground"
      />
      <span className="hidden md:inline">{t("askAi")}</span>
      {unread > 0 && (
        <span className="bg-destructive text-destructive-foreground absolute -top-1 -right-1 flex size-4 items-center justify-center text-[10px] font-semibold">
          {unread}
        </span>
      )}
    </Button>
  )
}
