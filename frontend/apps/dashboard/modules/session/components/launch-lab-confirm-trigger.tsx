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
import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"
import type { QueuedResult, SessionData } from "../types"
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
  const t = useTranslations("dashboard.session.launchLabConfirmTrigger")
  const tPending = useTranslations("dashboard.session.accountPending")
  const { status, result, launch, reset } = useLaunchLab(labSlug)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [phase, setPhase] = useState<Phase>("confirm")
  const [credsOpen, setCredsOpen] = useState(false)
  const [queueState, setQueueState] = useState<QueuedResult | null>(null)
  const [readySession, setReadySession] = useState<SessionData | null>(null)

  useEffect(() => {
    if (!result) return
    if (result.kind === "denied") {
      if (result.code === CONSENT_REQUIRED) setPhase("consent")
      else if (result.code === INACTIVE_ACCOUNT) setPhase("accountPending")
      else {
        setConfirmOpen(false)
        toast.error(result.detail)
      }
      return
    }
    setConfirmOpen(false)
    if (result.kind === "session") {
      setReadySession(result.session)
      setCredsOpen(true)
    } else {
      setQueueState(result.queued)
    }
  }, [result])

  const handleConsentAnswered = useCallback(() => {
    setPhase("confirm")
    launch()
  }, [launch])

  const handleQueueReady = useCallback((session: SessionData) => {
    setQueueState(null)
    setReadySession(session)
    setCredsOpen(true)
  }, [])

  const handleQueueCancel = useCallback(() => {
    setQueueState(null)
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

  return (
    <>
      <AlertDialog open={confirmOpen} onOpenChange={handleConfirmOpenChange}>
        <AlertDialogTrigger render={children} />
        <AlertDialogContent>
          {phase === "consent" && (
            <ConsentStep onAnswered={handleConsentAnswered} />
          )}
          {phase === "accountPending" && (
            <>
              <AlertDialogHeader>
                <AlertDialogTitle>{tPending("title")}</AlertDialogTitle>
                <AlertDialogDescription>
                  {tPending("description")}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>{tPending("close")}</AlertDialogCancel>
              </AlertDialogFooter>
            </>
          )}
          {phase === "confirm" && (
            <>
              <AlertDialogHeader>
                <AlertDialogTitle>{t("title")}</AlertDialogTitle>
                <AlertDialogDescription>
                  {t("description")}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel disabled={status === "launching"}>
                  {t("cancel")}
                </AlertDialogCancel>
                <AlertDialogAction
                  onClick={(e) => {
                    e.preventDefault()
                    track("session_launch_clicked", { lab_slug: labSlug })
                    launch()
                  }}
                  disabled={status === "launching"}
                >
                  {status === "launching" ? (
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
          )}
        </AlertDialogContent>
      </AlertDialog>
      {queueState && (
        <QueueWaitDialog
          labSlug={labSlug}
          initial={queueState}
          open={queueState !== null}
          onReady={handleQueueReady}
          onCancel={handleQueueCancel}
        />
      )}
      <CredentialsDialog
        result={readySession}
        open={credsOpen}
        onOpenChange={(v) => {
          setCredsOpen(v)
          if (!v) {
            setReadySession(null)
            reset()
          }
        }}
      />
    </>
  )
}
