"use client"

import { Button } from "@repo/design-system/ui/button"
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "@repo/design-system/ui/drawer"
import { ExternalLinkIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useTransition } from "react"
import { toast } from "sonner"
import type { Node } from "../types"

const STATUS_KEYS: Record<Node["status"], string> = {
  started: "started",
  stopped: "stopped",
  suspended: "suspended",
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
  const t = useTranslations("dashboard.session.nodeDetailDrawer")
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
              <DrawerDescription>
                {t(`status.${STATUS_KEYS[node.status]}`)}
              </DrawerDescription>
            </DrawerHeader>
            <div className="flex flex-col gap-2 p-4">
              {node.console !== null && (
                <Button
                  nativeButton={false}
                  className="w-full"
                  render={
                    // biome-ignore lint/a11y/useAnchorContent: content comes from the Base UI render slot
                    <a href={`telnet://${node.consoleHost}:${node.console}`} />
                  }
                >
                  {t("openConsole", {
                    type: node.consoleType ?? "",
                    port: node.console,
                  })}
                  <ExternalLinkIcon data-icon="inline-end" />
                </Button>
              )}
              {node.status === "started" ? (
                <Button
                  variant="outline"
                  disabled={pending}
                  onClick={() => run("stop", t("toastStopped"))}
                >
                  {t("stopNode")}
                </Button>
              ) : (
                <Button
                  variant="outline"
                  disabled={pending}
                  onClick={() => run("start", t("toastStarted"))}
                >
                  {t("startNode")}
                </Button>
              )}
              <Button
                variant="outline"
                disabled={pending}
                onClick={() => run("reload", t("toastReloaded"))}
              >
                {t("reloadNode")}
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
