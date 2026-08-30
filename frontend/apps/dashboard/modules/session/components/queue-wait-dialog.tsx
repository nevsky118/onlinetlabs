"use client"

import { formatEtaApprox } from "@/lib/format-duration"
import { Button } from "@repo/design-system/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@repo/design-system/ui/dialog"
import { Spinner } from "@repo/design-system/ui/spinner"
import { useTranslations } from "next-intl"
import type { QueuedResult, SessionData } from "../types"
import { QUEUE_POLL_INTERVAL_MS, useQueuePoll } from "../hooks/use-queue-poll"

export function QueueWaitDialog({
  labSlug,
  initial,
  open,
  onReady,
  onCancel,
}: {
  labSlug: string
  initial: QueuedResult
  open: boolean
  onReady: (session: SessionData) => void
  onCancel: () => void
}) {
  const t = useTranslations("dashboard.session.queueWaitDialog")
  const durationT = useTranslations("dashboard.session.duration")
  const queued = useQueuePoll({ labSlug, initial, enabled: open, onReady })

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) onCancel()
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-3 py-2">
          <div className="text-sm">
            {t.rich("position", {
              position: () => (
                <span className="font-medium tabular-nums">
                  {queued.position}
                </span>
              ),
              depth: () => (
                <span className="font-medium tabular-nums">{queued.depth}</span>
              ),
            })}
          </div>
          <div className="text-sm text-muted-foreground">
            {t("waiting", { eta: formatEtaApprox(queued.etaSec, durationT) })}
          </div>
          <div className="relative h-2 overflow-hidden rounded-none bg-muted">
            <div className="absolute inset-y-0 left-0 w-1/3 animate-[queue-shimmer_1.5s_ease-in-out_infinite] bg-primary/70" />
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Spinner />
            {t("checkingEvery", { seconds: QUEUE_POLL_INTERVAL_MS / 1000 })}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            {t("cancel")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
