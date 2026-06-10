"use client"

import { SparklesIcon } from "lucide-react"
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react"
import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"

export const CHAT_PANEL_DEFAULT_WIDTH = 450
export const CHAT_PANEL_MIN_WIDTH = 360

type ChatPanelContextValue = {
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
  const ctx = useContext(ChatPanelContext)
  if (!ctx) throw new Error("useChatPanel вне ChatPanelProvider")
  return ctx
}

export function ChatPanelProvider({
  children,
  defaultOpen = false,
}: {
  children: React.ReactNode
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

  const value = useMemo(
    () => ({
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
    [open, openPanel, closePanel, width, resizing, unread, bumpUnread]
  )

  return (
    <ChatPanelContext.Provider value={value}>
      {children}
    </ChatPanelContext.Provider>
  )
}

// Сдвигает контент влево при открытой панели, как в Cloudflare dash
export function ChatPanelInset({ children }: { children: React.ReactNode }) {
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

export function ChatPanelTrigger({ onOpen }: { onOpen?: () => void }) {
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
      <span className="hidden md:inline">Спросить ИИ</span>
      {unread > 0 && (
        <span className="bg-destructive text-destructive-foreground absolute -top-1 -right-1 flex size-4 items-center justify-center text-[10px] font-semibold">
          {unread}
        </span>
      )}
    </Button>
  )
}
