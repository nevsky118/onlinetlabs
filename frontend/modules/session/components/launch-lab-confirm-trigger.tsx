"use client"

import { useCallback, useEffect, useState } from "react"
import type { QueuedResult, SessionData } from "../types"
import { useLaunchLab } from "../hooks/use-launch-lab"
import { CredentialsDialog } from "./credentials-dialog"
import { QueueWaitDialog } from "./queue-wait-dialog"
import { track } from "@/lib/analytics"
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
import { Spinner } from "@/ui/spinner"

export function LaunchLabConfirmTrigger({
  labSlug,
  children,
}: {
  labSlug: string
  children: React.ReactElement
}) {
  const { status, result, launch, reset } = useLaunchLab(labSlug)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [credsOpen, setCredsOpen] = useState(false)
  const [queueState, setQueueState] = useState<QueuedResult | null>(null)
  const [readySession, setReadySession] = useState<SessionData | null>(null)

  useEffect(() => {
    if (!result) return
    setConfirmOpen(false)
    if (result.kind === "session") {
      setReadySession(result.session)
      setCredsOpen(true)
    } else {
      setQueueState(result.queued)
    }
  }, [result])

  const handleQueueReady = useCallback((session: SessionData) => {
    setQueueState(null)
    setReadySession(session)
    setCredsOpen(true)
  }, [])

  const handleQueueCancel = useCallback(() => {
    setQueueState(null)
    reset()
  }, [reset])

  return (
    <>
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogTrigger render={children} />
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Запустить лабораторию?</AlertDialogTitle>
            <AlertDialogDescription>
              Создаём выделенную среду GNS3. После завершения сессии прогресс не
              сохраняется — можно запустить заново.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={status === "launching"}>
              Отмена
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
                  Готовим окружение...
                </>
              ) : (
                "Запустить"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
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
