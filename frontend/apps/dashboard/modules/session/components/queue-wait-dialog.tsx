"use client"

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
import { useEffect, useRef, useState } from "react"
import type { QueuedResult, SessionData } from "../types"
import { launchLab } from "../actions"
import { formatEtaApprox } from "@/lib/format-duration"

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
  const [queued, setQueued] = useState<QueuedResult>(initial)
  const aliveRef = useRef(true)

  useEffect(() => {
    setQueued(initial)
  }, [initial])

  useEffect(() => {
    if (!open) return
    aliveRef.current = true

    const tick = async () => {
      try {
        const res = await launchLab(labSlug)
        if (!aliveRef.current) return
        if (res.kind === "session") {
          onReady(res.session)
        } else {
          setQueued(res.queued)
        }
      } catch {
        // swallow — keep polling
      }
    }

    const id = setInterval(tick, 5000)
    return () => {
      aliveRef.current = false
      clearInterval(id)
    }
  }, [open, labSlug, onReady])

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) onCancel()
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
          <div className="text-muted-foreground text-sm">
            {t("waiting", { eta: formatEtaApprox(queued.etaSec, durationT) })}
          </div>
          <div className="bg-muted relative h-2 overflow-hidden rounded-none">
            <div className="bg-primary/70 absolute inset-y-0 left-0 w-1/3 animate-[queue-shimmer_1.5s_ease-in-out_infinite]" />
          </div>
          <div className="text-muted-foreground flex items-center gap-2 text-xs">
            <Spinner />
            {t("checkingEvery", { seconds: 5 })}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            {t("cancel")}
          </Button>
        </DialogFooter>
      </DialogContent>
      <style jsx global>{`
        @keyframes queue-shimmer {
          0% {
            transform: translateX(-100%);
          }
          50% {
            transform: translateX(150%);
          }
          100% {
            transform: translateX(350%);
          }
        }
      `}</style>
    </Dialog>
  )
}
