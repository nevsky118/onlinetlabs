"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { recordStudyDecision, revokeStudyConsent } from "../api"
import { consentKeys, consentRecordsQuery } from "../query"

/**
 * Whether the signed-in student takes part in the study, plus the toggle. The
 * granted flag is `null` until the first read resolves.
 */
export function useStudyConsent() {
  const queryClient = useQueryClient()
  const { data: granted, isPending } = useQuery(consentRecordsQuery())

  const toggleMutation = useMutation({
    mutationFn: (next: boolean) =>
      next ? recordStudyDecision("granted") : revokeStudyConsent(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consentKeys.records() })
    },
  })

  return {
    // A failed read is reported as "not participating" rather than an endless
    // spinner: the toggle stays usable.
    granted: isPending ? null : (granted ?? false),
    toggle: toggleMutation.mutateAsync,
    isSaving: toggleMutation.isPending,
  }
}
