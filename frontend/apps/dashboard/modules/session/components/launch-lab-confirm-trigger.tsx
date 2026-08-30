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
import { Spinner } from "@repo/design-system/ui/spinner"
import { useTranslations } from "next-intl"
import { useCallback, useState } from "react"
import { toast } from "sonner"
import type { LaunchResult, QueuedResult, SessionData } from "../types"
import { useLaunchLab } from "../hooks/use-launch-lab"
import { ConsentStep } from "./consent-step"
import { CredentialsDialog } from "./credentials-dialog"
import { QueueWaitDialog } from "./queue-wait-dialog"

const CONSENT_REQUIRED = "error.consent.required"
const INACTIVE_ACCOUNT = "error.auth.inactive_account"

type Phase = "confirm" | "consent" | "accountPending"

export function LaunchLabConfirmTrigger({
  labSlug,
  children,
}: {
  labSlug: string
  children: React.ReactElement
}) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [phase, setPhase] = useState<Phase>("confirm")
  const [queued, setQueued] = useState<QueuedResult | null>(null)
  const [readySession, setReadySession] = useState<SessionData | null>(null)

  // The launch outcome is an event, handled here rather than in an effect
  // watching the last result.
  const handleResult = useCallback((result: LaunchResult) => {
    switch (result.kind) {
      case "denied":
        switch (result.code) {
          case CONSENT_REQUIRED:
            setPhase("consent")
            break
          case INACTIVE_ACCOUNT:
            setPhase("accountPending")
            break
          default:
            setConfirmOpen(false)
            toast.error(result.detail)
        }
        break
      case "session":
        setConfirmOpen(false)
        setReadySession(result.session)
        break
      case "queued":
        setConfirmOpen(false)
        setQueued(result.queued)
        break
    }
  }, [])

  const { status, launch, reset } = useLaunchLab(labSlug, handleResult)

  const handleConsentAnswered = useCallback(() => {
    setPhase("confirm")
    launch()
  }, [launch])

  const handleQueueReady = useCallback((session: SessionData) => {
    setQueued(null)
    setReadySession(session)
  }, [])

  const handleQueueCancel = useCallback(() => {
    setQueued(null)
    reset()
  }, [reset])

  const handleConfirmOpenChange = useCallback(
    (open: boolean) => {
      setConfirmOpen(open)
      if (!open) {
        setPhase("confirm")
        reset()
      }
    },
    [reset]
  )

  const handleCredentialsOpenChange = useCallback(
    (open: boolean) => {
      if (!open) {
        setReadySession(null)
        reset()
      }
    },
    [reset]
  )

  return (
    <>
      <AlertDialog open={confirmOpen} onOpenChange={handleConfirmOpenChange}>
        <AlertDialogTrigger render={children} />
        <AlertDialogContent>
          <LaunchPhaseStep
            phase={phase}
            labSlug={labSlug}
            launching={status === "launching"}
            onLaunch={launch}
            onConsentAnswered={handleConsentAnswered}
          />
        </AlertDialogContent>
      </AlertDialog>
      {queued && (
        <QueueWaitDialog
          labSlug={labSlug}
          initial={queued}
          open
          onReady={handleQueueReady}
          onCancel={handleQueueCancel}
        />
      )}
      <CredentialsDialog
        session={readySession}
        open={readySession !== null}
        onOpenChange={handleCredentialsOpenChange}
      />
    </>
  )
}

function LaunchPhaseStep({
  phase,
  labSlug,
  launching,
  onLaunch,
  onConsentAnswered,
}: {
  phase: Phase
  labSlug: string
  launching: boolean
  onLaunch: () => void
  onConsentAnswered: () => void
}) {
  switch (phase) {
    case "consent":
      return <ConsentStep onAnswered={onConsentAnswered} />
    case "accountPending":
      return <AccountPendingStep />
    case "confirm":
      return (
        <ConfirmStep
          labSlug={labSlug}
          launching={launching}
          onLaunch={onLaunch}
        />
      )
  }
}

function AccountPendingStep() {
  const t = useTranslations("dashboard.session.accountPending")

  return (
    <>
      <AlertDialogHeader>
        <AlertDialogTitle>{t("title")}</AlertDialogTitle>
        <AlertDialogDescription>{t("description")}</AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel>{t("close")}</AlertDialogCancel>
      </AlertDialogFooter>
    </>
  )
}

function ConfirmStep({
  labSlug,
  launching,
  onLaunch,
}: {
  labSlug: string
  launching: boolean
  onLaunch: () => void
}) {
  const t = useTranslations("dashboard.session.launchLabConfirmTrigger")

  return (
    <>
      <AlertDialogHeader>
        <AlertDialogTitle>{t("title")}</AlertDialogTitle>
        <AlertDialogDescription>{t("description")}</AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel disabled={launching}>
          {t("cancel")}
        </AlertDialogCancel>
        <AlertDialogAction
          disabled={launching}
          onClick={(event) => {
            event.preventDefault()
            track("session_launch_clicked", { lab_slug: labSlug })
            onLaunch()
          }}
        >
          {launching ? (
            <>
              <Spinner data-icon="inline-start" />
              {t("preparing")}
            </>
          ) : (
            t("launch")
          )}
        </AlertDialogAction>
      </AlertDialogFooter>
    </>
  )
}
