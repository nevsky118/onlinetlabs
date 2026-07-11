"use client"

import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"
import { toast } from "sonner"
import type { SessionStatus } from "../types"
import { endLab, resetLab, restartLab, stopLab } from "../actions"
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
} from "@/ui/alert-dialog"
import { Badge } from "@/ui/badge"
import { Button } from "@/ui/button"

export function LabControls({
  sessionId,
  status,
}: {
  sessionId: string
  status: SessionStatus
}) {
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
      } catch (e) {
        toast.error((e as Error).message)
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
        onClick={() => run(() => stopLab(sessionId), "Остановлено")}
      >
        Stop
      </Button>
      <Button
        variant="outline"
        disabled={disabled}
        onClick={() => run(() => restartLab(sessionId), "Перезапущено")}
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
            <AlertDialogTitle>Сбросить лабу?</AlertDialogTitle>
            <AlertDialogDescription>
              Проект будет пересоздан из шаблона. Текущий прогресс в топологии
              потеряется.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => run(() => resetLab(sessionId), "Сброшено")}
            >
              Сбросить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog>
        <AlertDialogTrigger
          render={<Button variant="destructive" disabled={disabled} />}
        >
          Завершить
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Завершить сессию?</AlertDialogTitle>
            <AlertDialogDescription>
              GNS3-окружение будет удалено. Действие необратимо.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                run(async () => {
                  await endLab(sessionId)
                  setCurrent("ended")
                }, "Сессия завершена")
              }
            >
              Завершить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
