"use client"

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
import { useState } from "react"
import type { AgentActivityEvent } from "../types"
import { useAgentActivity } from "../hooks/use-agent-activity"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/ui/collapsible"

// Иконка по kind события
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
    const d = new Date(ts)
    return d.toTimeString().slice(0, 8)
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
        <span className="text-muted-foreground font-mono text-xs shrink-0">
          [{formatTime(event.ts)}]
        </span>
        <span className="text-muted-foreground shrink-0 mt-px">
          {kindIcon(event.kind)}
        </span>
        <span className="text-foreground font-mono text-xs leading-relaxed">
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
            className="flex w-full items-start gap-1.5 px-3 py-0.5 text-left hover:bg-muted/50 transition-colors"
          />
        }
      >
        <span className="text-muted-foreground font-mono text-xs shrink-0">
          [{formatTime(event.ts)}]
        </span>
        <span className="text-muted-foreground shrink-0 mt-px">
          {kindIcon(event.kind)}
        </span>
        <span className="text-foreground font-mono text-xs leading-relaxed flex-1">
          {event.summary}
        </span>
        <span className="text-muted-foreground shrink-0 mt-px">
          {open ? (
            <ChevronDownIcon className="size-3" />
          ) : (
            <ChevronRightIcon className="size-3" />
          )}
        </span>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <pre className="text-xs text-muted-foreground font-mono px-3 pb-1 overflow-x-auto whitespace-pre-wrap break-all bg-muted/30">
          {Object.entries(event.detail ?? {})
            .map(
              ([k, v]) =>
                `${k}: ${typeof v === "object" ? JSON.stringify(v) : String(v)}`
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
  const { events } = useAgentActivity(sessionId, enabled)

  if (!enabled) return null

  return (
    <div className="border-t bg-background flex flex-col">
      {/* Заголовок */}
      <div className="flex items-center gap-2 border-b px-3 py-2">
        <BotIcon className="size-3.5 text-muted-foreground shrink-0" />
        <span className="text-xs font-medium">Активность ИИ</span>
        {events.length > 0 && (
          <span className="ml-auto text-xs text-muted-foreground tabular-nums">
            {events.length}
          </span>
        )}
      </div>
      {/* Список событий */}
      <div className="overflow-y-auto max-h-64 flex flex-col">
        {events.length === 0 ? (
          <p className="text-muted-foreground text-xs px-3 py-2">Нет событий</p>
        ) : (
          [...events]
            .reverse()
            .map((event) => <AgentActivityLine key={event.id} event={event} />)
        )}
      </div>
    </div>
  )
}
