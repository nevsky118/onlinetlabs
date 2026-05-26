"use client"

import { useTransition } from "react"
import { toast } from "sonner"
import type { Node } from "../types"
import { track } from "@/lib/analytics"
import { Button } from "@/ui/button"
import { Skeleton } from "@/ui/skeleton"

const STATUS_COLOR: Record<Node["status"], string> = {
  started: "bg-emerald-500",
  stopped: "bg-muted-foreground",
  suspended: "bg-amber-500",
}

export function NodesCard({
  nodes,
  disabled,
  loading,
  onAction,
  onOpenDetails,
}: {
  nodes: Node[]
  disabled: boolean
  loading: boolean
  onAction: (nodeId: string, action: string) => Promise<void>
  onOpenDetails: (nodeId: string) => void
}) {
  if (loading) {
    return (
      <div className="bg-card border p-4">
        <Skeleton className="h-3 w-20" />
        <div className="mt-3 flex flex-col gap-2">
          <Skeleton className="h-6" />
          <Skeleton className="h-6" />
          <Skeleton className="h-6" />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card border p-4">
      <div className="text-muted-foreground mb-3 text-xs tracking-wide uppercase">
        Узлы · {nodes.filter((n) => n.status === "started").length} /{" "}
        {nodes.length} запущено
      </div>
      {nodes.length === 0 ? (
        <div className="text-muted-foreground py-6 text-center text-sm">
          Узлы не настроены
        </div>
      ) : (
        <ul className="divide-y">
          {nodes.map((n) => (
            <NodeRow
              key={n.id}
              node={n}
              disabled={disabled}
              onAction={onAction}
              onOpenDetails={onOpenDetails}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function NodeRow({
  node,
  disabled,
  onAction,
  onOpenDetails,
}: {
  node: Node
  disabled: boolean
  onAction: (nodeId: string, action: string) => Promise<void>
  onOpenDetails: (nodeId: string) => void
}) {
  const [pending, startTransition] = useTransition()
  const isStarted = node.status === "started"

  const toggle = () =>
    startTransition(async () => {
      try {
        const action = isStarted ? "stop" : "start"
        await onAction(node.id, action)
        track("node_action_triggered", { action, node_id: node.id })
        toast.success(isStarted ? "Узел остановлен" : "Узел запущен")
      } catch (e) {
        toast.error((e as Error).message)
      }
    })

  return (
    <li className="flex items-center gap-3 py-2.5 text-sm">
      <span className={`size-2 rounded-full ${STATUS_COLOR[node.status]}`} />
      <button
        type="button"
        onClick={() => onOpenDetails(node.id)}
        className="font-medium hover:underline md:cursor-default md:hover:no-underline"
      >
        {node.name}
      </button>
      <span className="text-muted-foreground text-xs">{node.nodeType}</span>
      {node.console !== null && (
        <code className="text-muted-foreground ml-auto hidden font-mono text-xs md:inline">
          :{node.console}
        </code>
      )}
      <Button
        variant="outline"
        size="sm"
        className="ml-auto h-7 rounded-none px-2 text-[0.75rem] md:ml-2"
        disabled={disabled || pending}
        onClick={toggle}
      >
        {isStarted ? "Остановить" : "Запустить"}
      </Button>
    </li>
  )
}
