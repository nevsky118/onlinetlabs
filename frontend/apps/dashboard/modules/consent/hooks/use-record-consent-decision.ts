"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { ConsentDecision } from "../types"
import { recordStudyDecision } from "../api"
import { consentKeys } from "../query"

/**
 * Persists the accept/decline answer a student gives in the consent step.
 * Outcomes are reported through callbacks so the wording stays with the view.
 */
export function useRecordConsentDecision({
  onRecorded,
  onFailed,
}: {
  onRecorded: (decision: ConsentDecision) => void
  onFailed: () => void
}) {
  const queryClient = useQueryClient()

  const decisionMutation = useMutation({
    mutationFn: recordStudyDecision,
    onSuccess: (_result, decision) => {
      queryClient.invalidateQueries({ queryKey: consentKeys.records() })
      onRecorded(decision)
    },
    onError: onFailed,
  })

  return {
    record: decisionMutation.mutate,
    pendingDecision: decisionMutation.isPending
      ? decisionMutation.variables
      : null,
  }
}
