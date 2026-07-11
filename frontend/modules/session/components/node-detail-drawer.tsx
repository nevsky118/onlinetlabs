"use client"

import { ExternalLinkIcon } from "lucide-react"
import { useTransition } from "react"
import { toast } from "sonner"
import type { Node } from "../types"
import { Button } from "@/ui/button"
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "@/ui/drawer"

const STATUS_LABEL: Record<Node["status"], string> = {
  started: "Запущен",
  stopped: "Остановлен",
  suspended: "Приостановлен",
}

export function NodeDetailDrawer({
  nodeId,
  nodes,
  onClose,
  onAction,
}: {
  nodeId: string | null
  nodes: Node[]
  onClose: () => void
  onAction: (nodeId: string, action: string) => Promise<void>
}) {
  const node = nodes.find((n) => n.id === nodeId)
  const [pending, startTransition] = useTransition()

  const run = (action: string, ok: string) =>
    startTransition(async () => {
      if (!node) return
      try {
        await onAction(node.id, action)
        toast.success(ok)
        onClose()
      } catch (e) {
        toast.error((e as Error).message)
      }
    })

  return (
    <Drawer open={node !== undefined} onOpenChange={(o) => !o && onClose()}>
      <DrawerContent>
        {node && (
          <>
            <DrawerHeader>
              <DrawerTitle>
                {node.name} · {node.nodeType}
              </DrawerTitle>
              <DrawerDescription>{STATUS_LABEL[node.status]}</DrawerDescription>
            </DrawerHeader>
            <div className="flex flex-col gap-2 p-4">
              {node.console !== null && (
                <Button
                  nativeButton={false}
                  className="w-full"
                  render={
                    // biome-ignore lint/a11y/useAnchorContent: контент приходит из render-слота Base UI
                    <a href={`telnet://${node.consoleHost}:${node.console}`} />
                  }
                >
                  Открыть консоль ({node.consoleType}:{node.console})
                  <ExternalLinkIcon data-icon="inline-end" />
                </Button>
              )}
              {node.status === "started" ? (
                <Button
                  variant="outline"
                  disabled={pending}
                  onClick={() => run("stop", "Узел остановлен")}
                >
                  Остановить узел
                </Button>
              ) : (
                <Button
                  variant="outline"
                  disabled={pending}
                  onClick={() => run("start", "Узел запущен")}
                >
                  Запустить узел
                </Button>
              )}
              <Button
                variant="outline"
                disabled={pending}
                onClick={() => run("reload", "Узел перезагружен")}
              >
                Перезагрузить узел
              </Button>
            </div>
            <DrawerFooter>
              <div className="text-muted-foreground space-y-1 text-xs">
                <div>
                  <span className="font-mono">id</span> · {node.id}
                </div>
                <div>
                  <span className="font-mono">host</span> · {node.consoleHost}
                </div>
              </div>
            </DrawerFooter>
          </>
        )}
      </DrawerContent>
    </Drawer>
  )
}
