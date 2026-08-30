"use client"

import { authClient } from "@repo/auth/client"
import { useMutation, useQuery } from "@tanstack/react-query"
import { revokeOtherSessions } from "../api"
import { accountSessionsQuery } from "../query"

/** Active session count plus the two sign-out paths. */
export function useAccountSessions(onSignOutFailed: () => void) {
  const { data: activeCount } = useQuery(accountSessionsQuery())

  const signOutEverywhereMutation = useMutation({
    mutationFn: async () => {
      await revokeOtherSessions()
      await authClient.signOut()
      window.location.href = "/"
    },
    onError: onSignOutFailed,
  })

  const signOutMutation = useMutation({
    mutationFn: async () => {
      await authClient.signOut()
      window.location.href = "/"
    },
    onError: onSignOutFailed,
  })

  return {
    activeCount: activeCount ?? null,
    signOutEverywhere: signOutEverywhereMutation.mutate,
    signOut: signOutMutation.mutate,
    isBusy: signOutEverywhereMutation.isPending || signOutMutation.isPending,
  }
}
