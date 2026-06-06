"use client"

import { ExternalLinkIcon } from "lucide-react"
import Link from "next/link"
import { useTransition } from "react"
import { toast } from "sonner"
import type { Session } from "../types"
import { endLab } from "../actions"
import { SessionStatusBadge } from "./session-status-badge"
import { cn } from "@/lib/utils"
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
import { Button } from "@/ui/button"
import { Spinner } from "@/ui/spinner"

type Props = {
  session: Session
  /** секунды с момента startedAt, считает родитель */
  uptimeSeconds: number
  onEnded: () => void
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds} сек`
  const mins = Math.floor(seconds / 60)
  if (mins < 60) return `${mins} мин`
  const hrs = Math.floor(mins / 60)
  const rem = mins % 60
  return rem > 0 ? `${hrs} ч ${rem} мин` : `${hrs} ч`
}

function formatRelative(isoString: string): string {
  const diff = Math.max(
    0,
    Math.floor((Date.now() - new Date(isoString).getTime()) / 1000)
  )
  if (diff < 60) return "только что"
  const mins = Math.floor(diff / 60)
  if (mins < 60) return `${mins} мин назад`
  const hrs = Math.floor(mins / 60)
  return `${hrs} ч назад`
}

export function SessionCard({ session, uptimeSeconds, onEnded }: Props) {
  const [pending, startTransition] = useTransition()
  const title = session.labTitle ?? session.labSlug
  const isActive = session.status === "active"
  const isProvisioning = session.status === "provisioning"
  const isRunning = isActive || isProvisioning

  function handleEnd() {
    startTransition(async () => {
      try {
        await endLab(session.id)
        toast.success("Сессия завершена")
        onEnded()
      } catch {
        toast.error("Не удалось завершить сессию")
      }
    })
  }

  return (
    <article className="border bg-card p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-1 min-w-0">
          <h3 className="font-medium truncate">{title}</h3>
          <p className="text-muted-foreground text-xs">
            {isRunning ? (
              <>
                запущена {formatRelative(session.startedAt)} ·{" "}
                {formatUptime(uptimeSeconds)}
              </>
            ) : session.endedAt ? (
              <>завершена {formatRelative(session.endedAt)}</>
            ) : (
              <>запущена {formatRelative(session.startedAt)}</>
            )}
          </p>
        </div>
        <SessionStatusBadge status={session.status} />
      </div>

      <div className="flex items-center gap-2">
        {isRunning && (
          <Button variant="default" size="sm" className="rounded-none" asChild>
            <Link href={`/session/${session.id}`}>
              <ExternalLinkIcon data-icon="inline-start" />
              Открыть
            </Link>
          </Button>
        )}

        {isProvisioning && (
          <span className="text-muted-foreground flex items-center gap-1.5 text-xs">
            <Spinner className="size-3" />
            Готовится…
          </span>
        )}

        {isRunning && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="rounded-none"
                disabled={pending}
              >
                {pending ? (
                  <Spinner data-icon="inline-start" className="size-3" />
                ) : null}
                Завершить
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Завершить сессию?</AlertDialogTitle>
                <AlertDialogDescription>
                  Лаборатория «{title}» будет остановлена. Несохранённый
                  прогресс может быть утерян.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Отмена</AlertDialogCancel>
                <AlertDialogAction variant="destructive" onClick={handleEnd}>
                  Завершить
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}

        {!isRunning && (
          <Button variant="outline" size="sm" className="rounded-none" asChild>
            <Link href={`/labs/${session.labSlug}`}>Запустить снова</Link>
          </Button>
        )}
      </div>
    </article>
  )
}
