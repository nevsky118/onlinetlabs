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
import { Button } from "@repo/design-system/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@repo/design-system/ui/dropdown-menu"
import { Link } from "@repo/i18n/navigation"
import {
  BookOpenIcon,
  MoreVerticalIcon,
  RefreshCcwIcon,
  XIcon,
} from "lucide-react"
import { useTranslations } from "next-intl"
import type { SessionStatus } from "../types"
import { useSessionControls } from "../hooks/use-session-controls"

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
  const { reset, end, isBusy } = useSessionControls(sessionId, labSlug)

  const disabled = isBusy || status === "ended"

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
        <ResetButton disabled={disabled} onConfirm={() => reset()} />
        <EndButton disabled={disabled} onConfirm={() => end()} />
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
              <DropdownMenuItem disabled={disabled} onClick={() => reset()}>
                <RefreshCcwIcon /> {t("reset")}
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={disabled}
                onClick={() => end()}
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
