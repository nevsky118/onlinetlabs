"use client"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@repo/design-system/ui/alert-dialog"
import { Badge } from "@repo/design-system/ui/badge"
import { Button } from "@repo/design-system/ui/button"
import { useTranslations } from "next-intl"
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"
import { toast } from "sonner"
import type { SessionStatus } from "../types"
import { endLab, resetLab, restartLab, stopLab } from "../actions"

export function LabControls({
  sessionId,
  status,
}: {
  sessionId: string
  status: SessionStatus
}) {
  const t = useTranslations("dashboard.session.labControls")
  const router = useRouter()
  const [pending, startTransition] = useTransition()
  const [current, setCurrent] = useState<SessionStatus>(status)
  const disabled = pending || current === "ended"

  function run(fn: () => Promise<void>, ok: string) {
    startTransition(async () => {
      try {
        await fn()
        toast.success(ok)
        router.refresh()
      } catch (error) {
        toast.error((error as Error).message)
      }
    })
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant={current === "active" ? "default" : "secondary"}>
        {current}
      </Badge>
      <Button
        variant="outline"
        disabled={disabled}
        onClick={() => run(() => stopLab(sessionId), t("toastStopped"))}
      >
        Stop
      </Button>
      <Button
        variant="outline"
        disabled={disabled}
        onClick={() => run(() => restartLab(sessionId), t("toastRestarted"))}
      >
        Restart
      </Button>

      <AlertDialog>
        <AlertDialogTrigger
          render={<Button variant="outline" disabled={disabled} />}
        >
          Reset
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("resetConfirmTitle")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("resetConfirmDescription")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => run(() => resetLab(sessionId), t("toastReset"))}
            >
              {t("reset")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog>
        <AlertDialogTrigger
          render={<Button variant="destructive" disabled={disabled} />}
        >
          {t("end")}
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("endConfirmTitle")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("endConfirmDescription")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                run(async () => {
                  await endLab(sessionId)
                  setCurrent("ended")
                }, t("toastEnded"))
              }
            >
              {t("end")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
