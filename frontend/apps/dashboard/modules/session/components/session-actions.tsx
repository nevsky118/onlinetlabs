"use client"

import { track } from "@repo/api/analytics"
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@repo/design-system/ui/dropdown-menu"
import { Link } from "@repo/i18n/navigation"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  BookOpenIcon,
  MoreVerticalIcon,
  RefreshCcwIcon,
  XIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import type { SessionStatus } from "../types"
import { endLab, resetLab } from "../actions"
import { sessionKeys } from "../query"

export function SessionActions({
  sessionId,
  status,
  labSlug,
}: {
  sessionId: string
  status: SessionStatus
  labSlug: string
}) {
  const t = useTranslations("dashboard.session.sessionActions")
  const qc = useQueryClient()

  const resetM = useMutation({
    mutationFn: () => resetLab(sessionId),
    onSuccess: () => {
      track("session_reset", { lab_slug: labSlug, session_id: sessionId })
      qc.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })
      toast.success(t("toastReset"))
    },
    onError: (e) => toast.error((e as Error).message),
  })

  const endM = useMutation({
    mutationFn: () => endLab(sessionId),
    onSuccess: () => {
      track("session_ended", {
        lab_slug: labSlug,
        session_id: sessionId,
        reason: "user",
      })
      qc.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })
      qc.invalidateQueries({ queryKey: sessionKeys.list() })
      toast.success(t("toastEnded"))
    },
    onError: (e) => toast.error((e as Error).message),
  })

  const disabled = resetM.isPending || endM.isPending || status === "ended"
  const runReset = () => resetM.mutate()
  const runEnd = () => endM.mutate()

  return (
    <div className="flex shrink-0 items-center gap-2">
      {/* Desktop: full row of buttons. */}
      <Button
        nativeButton={false}
        variant="outline"
        size="sm"
        className="hidden rounded-none md:inline-flex"
        render={<Link href={`/labs/${labSlug}`} />}
      >
        <BookOpenIcon data-icon="inline-start" />
        {t("instructions")}
      </Button>
      <div className="hidden gap-2 md:flex">
        <ResetButton disabled={disabled} onConfirm={runReset} />
        <EndButton disabled={disabled} onConfirm={runEnd} />
      </div>
      {/* Mobile: all 3 actions consolidated into a kebab menu. */}
      <div className="md:hidden">
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button
                variant="outline"
                size="icon"
                className="rounded-none"
                aria-label={t("actionsMenu")}
              />
            }
          >
            <MoreVerticalIcon />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuGroup>
              <DropdownMenuItem render={<Link href={`/labs/${labSlug}`} />}>
                <BookOpenIcon /> {t("instructions")}
              </DropdownMenuItem>
              <DropdownMenuItem disabled={disabled} onClick={runReset}>
                <RefreshCcwIcon /> {t("reset")}
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={disabled}
                onClick={runEnd}
                className="text-destructive"
              >
                <XIcon /> {t("end")}
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}

function ResetButton({
  disabled,
  onConfirm,
}: {
  disabled: boolean
  onConfirm: () => void
}) {
  const t = useTranslations("dashboard.session.sessionActions")
  return (
    <AlertDialog>
      <AlertDialogTrigger
        render={
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            className="rounded-none"
          />
        }
      >
        <RefreshCcwIcon data-icon="inline-start" /> {t("reset")}
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
          <AlertDialogAction onClick={onConfirm}>
            {t("reset")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

function EndButton({
  disabled,
  onConfirm,
}: {
  disabled: boolean
  onConfirm: () => void
}) {
  const t = useTranslations("dashboard.session.sessionActions")
  return (
    <AlertDialog>
      <AlertDialogTrigger
        render={
          <Button
            variant="destructive"
            size="sm"
            disabled={disabled}
            className="rounded-none"
          />
        }
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
          <AlertDialogAction onClick={onConfirm}>{t("end")}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
