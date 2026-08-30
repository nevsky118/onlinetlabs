"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { bulkNodeAction } from "../actions"
import { sessionKeys } from "../query"

/** Starts every paused node of a session back up. */
export function useResumeSession(sessionId: string) {
  const t = useTranslations("dashboard.session.pausedNotice")
  const queryClient = useQueryClient()

  const resumeMutation = useMutation({
    mutationFn: () => bulkNodeAction(sessionId, "start"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })
      toast.success(t("toastResumed"))
    },
    onError: () => toast.error(t("toastFailed")),
  })

  return {
    resume: resumeMutation.mutate,
    isResuming: resumeMutation.isPending,
  }
}
