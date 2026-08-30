"use client"

import { track } from "@repo/api/analytics"
import { Button } from "@repo/design-system/ui/button"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { useTranslations } from "next-intl"
import { useTransition } from "react"
import { toast } from "sonner"
import type { Node } from "../types"

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
  const t = useTranslations("dashboard.session.nodesCard")
  if (loading) {
    return (
      <div className="border bg-card p-4">
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
    <div className="border bg-card p-4">
      <div className="mb-3 text-xs tracking-wide text-muted-foreground uppercase">
        {t("heading", {
          started: nodes.filter((node) => node.status === "started").length,
          total: nodes.length,
        })}
      </div>
      {nodes.length === 0 ? (
        <div className="py-6 text-center text-sm text-muted-foreground">
          {t("empty")}
        </div>
      ) : (
        <ul className="divide-y">
          {nodes.map((node) => (
            <NodeRow
              key={node.id}
              node={node}
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
  const t = useTranslations("dashboard.session.nodesCard")
  const [pending, startTransition] = useTransition()
  const isStarted = node.status === "started"

  const toggle = () =>
    startTransition(async () => {
      try {
        const action = isStarted ? "stop" : "start"
        await onAction(node.id, action)
        track("node_action_triggered", { action, node_id: node.id })
        toast.success(isStarted ? t("toastStopped") : t("toastStarted"))
      } catch {
        /* the error is shown through the mutation's onError */
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
      <span className="text-xs text-muted-foreground">{node.nodeType}</span>
      {node.console !== null && (
        <code className="ml-auto hidden font-mono text-xs text-muted-foreground md:inline">
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
        {isStarted ? t("stop") : t("start")}
      </Button>
    </li>
  )
}
