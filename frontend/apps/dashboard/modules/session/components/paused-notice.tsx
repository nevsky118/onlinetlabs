"use client"

import {
  Alert,
  AlertAction,
  AlertDescription,
  AlertTitle,
} from "@repo/design-system/ui/alert"
import { Button } from "@repo/design-system/ui/button"
import { Spinner } from "@repo/design-system/ui/spinner"
import { PauseIcon, PlayIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useResumeSession } from "../hooks/use-resume-session"

export function PausedNotice({ sessionId }: { sessionId: string }) {
  const t = useTranslations("dashboard.session.pausedNotice")
  const { resume, isResuming } = useResumeSession(sessionId)

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
          disabled={isResuming}
          onClick={() => resume()}
        >
          {isResuming ? (
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
