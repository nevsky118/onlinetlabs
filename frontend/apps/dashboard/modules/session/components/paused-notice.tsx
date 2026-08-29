"use client"

import {
  Alert,
  AlertAction,
  AlertDescription,
  AlertTitle,
} from "@repo/design-system/ui/alert"
import { Button } from "@repo/design-system/ui/button"
import { Spinner } from "@repo/design-system/ui/spinner"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { PauseIcon, PlayIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { bulkNodeAction } from "../actions"
import { sessionKeys } from "../query"

export function PausedNotice({ sessionId }: { sessionId: string }) {
  const t = useTranslations("dashboard.session.pausedNotice")
  const qc = useQueryClient()

  const resume = useMutation({
    mutationFn: () => bulkNodeAction(sessionId, "start"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })
      toast.success(t("toastResumed"))
    },
    onError: () => toast.error(t("toastFailed")),
  })

  return (
    <Alert>
      <PauseIcon />
      <AlertTitle>{t("title")}</AlertTitle>
      <AlertDescription>{t("description")}</AlertDescription>
      <AlertAction>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={resume.isPending}
          onClick={() => resume.mutate()}
        >
          {resume.isPending ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <PlayIcon data-icon="inline-start" />
          )}
          {t("resume")}
        </Button>
      </AlertAction>
    </Alert>
  )
}
