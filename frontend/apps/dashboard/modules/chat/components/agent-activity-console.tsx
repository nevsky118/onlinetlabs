"use client"

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@repo/design-system/ui/collapsible"
import {
  AlertTriangleIcon,
  BotIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CpuIcon,
  NetworkIcon,
  WrenchIcon,
  ZapIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import type { AgentActivityEvent } from "../types"
import { useAgentActivity } from "../hooks/use-agent-activity"

// Icon by event kind
function kindIcon(kind: string) {
  switch (kind) {
    case "model_selected":
      return <CpuIcon className="size-3 shrink-0" />
    case "mcp_context_fetched":
      return <NetworkIcon className="size-3 shrink-0" />
    case "tool_call":
    case "tool_result":
      return <WrenchIcon className="size-3 shrink-0" />
    case "struggle_detected":
    case "error":
      return <AlertTriangleIcon className="size-3 shrink-0" />
    case "dispatched":
    case "agent_invoked":
      return <ZapIcon className="size-3 shrink-0" />
    default:
      return <BotIcon className="size-3 shrink-0" />
  }
}

function formatTime(ts: string): string {
  try {
    const date = new Date(ts)
    return date.toTimeString().slice(0, 8)
  } catch {
    return "--:--:--"
  }
}

export function AgentActivityLine({ event }: { event: AgentActivityEvent }) {
  const [open, setOpen] = useState(false)
  const hasDetail = event.detail && Object.keys(event.detail).length > 0

  if (!hasDetail) {
    return (
      <div className="flex items-start gap-1.5 px-3 py-0.5">
        <span className="shrink-0 font-mono text-xs text-muted-foreground">
          [{formatTime(event.ts)}]
        </span>
        <span className="mt-px shrink-0 text-muted-foreground">
          {kindIcon(event.kind)}
        </span>
        <span className="font-mono text-xs leading-relaxed text-foreground">
          {event.summary}
        </span>
      </div>
    )
  }

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger
        render={
          <button
            type="button"
            className="flex w-full items-start gap-1.5 px-3 py-0.5 text-left transition-colors hover:bg-muted/50"
          />
        }
      >
        <span className="shrink-0 font-mono text-xs text-muted-foreground">
          [{formatTime(event.ts)}]
        </span>
        <span className="mt-px shrink-0 text-muted-foreground">
          {kindIcon(event.kind)}
        </span>
        <span className="flex-1 font-mono text-xs leading-relaxed text-foreground">
          {event.summary}
        </span>
        <span className="mt-px shrink-0 text-muted-foreground">
          {open ? (
            <ChevronDownIcon className="size-3" />
          ) : (
            <ChevronRightIcon className="size-3" />
          )}
        </span>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <pre className="overflow-x-auto bg-muted/30 px-3 pb-1 font-mono text-xs break-all whitespace-pre-wrap text-muted-foreground">
          {Object.entries(event.detail ?? {})
            .map(
              ([key, value]) =>
                `${key}: ${typeof value === "object" ? JSON.stringify(value) : String(value)}`
            )
            .join("\n")}
        </pre>
      </CollapsibleContent>
    </Collapsible>
  )
}

interface AgentActivityConsoleProps {
  sessionId: string
  enabled: boolean
}

export function AgentActivityConsole({
  sessionId,
  enabled,
}: AgentActivityConsoleProps) {
  const t = useTranslations("dashboard.chat.agentActivityConsole")
  const { events } = useAgentActivity(sessionId, enabled)

  if (!enabled) return null

  return (
    <div className="flex flex-col border-t bg-background">
      {/* Heading */}
      <div className="flex items-center gap-2 border-b px-3 py-2">
        <BotIcon className="size-3.5 shrink-0 text-muted-foreground" />
        <span className="text-xs font-medium">{t("heading")}</span>
        {events.length > 0 && (
          <span className="ml-auto text-xs text-muted-foreground tabular-nums">
            {events.length}
          </span>
        )}
      </div>
      {/* Event list */}
      <div className="flex max-h-64 flex-col overflow-y-auto">
        {events.length === 0 ? (
          <p className="px-3 py-2 text-xs text-muted-foreground">
            {t("empty")}
          </p>
        ) : (
          events
            .toReversed()
            .map((event) => <AgentActivityLine key={event.id} event={event} />)
        )}
      </div>
    </div>
  )
}
