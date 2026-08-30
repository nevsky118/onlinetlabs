"use client"

import { formatDurationCoarse, formatRelativeTime } from "@/lib/format-duration"
import { LabProgressBadge, useLabProgress } from "@/modules/progress"
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
import { Button } from "@repo/design-system/ui/button"
import { Spinner } from "@repo/design-system/ui/spinner"
import { Link } from "@repo/i18n/navigation"
import { ExternalLinkIcon } from "lucide-react"
import { useFormatter, useTranslations } from "next-intl"
import { useTransition } from "react"
import { toast } from "sonner"
import type { Session } from "../types"
import { endLab } from "../actions"
import { SessionStatusBadge } from "./session-status-badge"

type Props = {
  session: Session
  /** seconds since startedAt, counted by the parent */
  uptimeSeconds: number
  onEnded: () => void
}

export function SessionCard({ session, uptimeSeconds, onEnded }: Props) {
  const t = useTranslations("dashboard.session.sessionCard")
  const durationT = useTranslations("dashboard.session.duration")
  const format = useFormatter()
  const [pending, startTransition] = useTransition()
  const { progress } = useLabProgress(session.labSlug)
  const title = session.labTitle ?? session.labSlug
  const isActive = session.status === "active"
  const isProvisioning = session.status === "provisioning"
  const isRunning = isActive || isProvisioning

  function handleEnd() {
    startTransition(async () => {
      try {
        await endLab(session.id)
        toast.success(t("toastEnded"))
        onEnded()
      } catch {
        toast.error(t("toastEndFailed"))
      }
    })
  }

  return (
    <article className="flex flex-col gap-3 border bg-card p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 flex-col gap-1">
          <div className="flex min-w-0 items-center gap-2">
            <h3 className="truncate font-medium">{title}</h3>
            <LabProgressBadge progress={progress} className="shrink-0" />
          </div>
          <p className="text-xs text-muted-foreground">
            {isRunning ? (
              <>
                {t("startedAt", {
                  when: formatRelativeTime(session.startedAt, format),
                })}{" "}
                · {formatDurationCoarse(uptimeSeconds, durationT)}
              </>
            ) : session.endedAt ? (
              t("endedAt", {
                when: formatRelativeTime(session.endedAt, format),
              })
            ) : (
              t("startedAt", {
                when: formatRelativeTime(session.startedAt, format),
              })
            )}
          </p>
        </div>
        <SessionStatusBadge status={session.status} />
      </div>

      <div className="flex items-center gap-2">
        {isRunning && (
          <Button
            nativeButton={false}
            variant="default"
            size="sm"
            className="rounded-none"
            render={<Link href={`/session/${session.id}`} />}
          >
            <ExternalLinkIcon data-icon="inline-start" />
            {t("open")}
          </Button>
        )}

        {isProvisioning && (
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Spinner className="size-3" />
            {t("provisioning")}
          </span>
        )}

        {isRunning && (
          <AlertDialog>
            <AlertDialogTrigger
              render={
                <Button
                  variant="outline"
                  size="sm"
                  className="rounded-none"
                  disabled={pending}
                />
              }
            >
              {pending ? (
                <Spinner data-icon="inline-start" className="size-3" />
              ) : null}
              {t("end")}
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>{t("endConfirmTitle")}</AlertDialogTitle>
                <AlertDialogDescription>
                  {t("endConfirmDescription", { title })}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>{t("cancel")}</AlertDialogCancel>
                <AlertDialogAction variant="destructive" onClick={handleEnd}>
                  {t("end")}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}

        {!isRunning && (
          <Button
            nativeButton={false}
            variant="outline"
            size="sm"
            className="rounded-none"
            render={<Link href={`/labs/${session.labSlug}`} />}
          >
            {t("launchAgain")}
          </Button>
        )}
      </div>
    </article>
  )
}
