"use client"

import { track } from "@repo/api/analytics"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { endLab, resetLab } from "../actions"
import { sessionKeys } from "../query"

function reportFailure(error: Error) {
  toast.error(error.message)
}

/** Destructive session-wide controls: reset the topology, end the session. */
export function useSessionControls(sessionId: string, labSlug: string) {
  const t = useTranslations("dashboard.session.sessionActions")
  const queryClient = useQueryClient()

  const resetMutation = useMutation({
    mutationFn: () => resetLab(sessionId),
    onSuccess: () => {
      track("session_reset", { lab_slug: labSlug, session_id: sessionId })
      queryClient.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })
      toast.success(t("toastReset"))
    },
    onError: reportFailure,
  })

  const endMutation = useMutation({
    mutationFn: () => endLab(sessionId),
    onSuccess: () => {
      track("session_ended", {
        lab_slug: labSlug,
        session_id: sessionId,
        reason: "user",
      })
      queryClient.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })
      queryClient.invalidateQueries({ queryKey: sessionKeys.list() })
      toast.success(t("toastEnded"))
    },
    onError: reportFailure,
  })

  return {
    reset: resetMutation.mutate,
    end: endMutation.mutate,
    isBusy: resetMutation.isPending || endMutation.isPending,
  }
}
