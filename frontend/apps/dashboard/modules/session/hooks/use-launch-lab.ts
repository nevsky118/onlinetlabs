"use client"

import { track } from "@repo/api/analytics"
import { useMutation } from "@tanstack/react-query"
import { toast } from "sonner"
import type { LaunchResult } from "../types"
import { launchLab } from "../actions"

export type LaunchStatus = "idle" | "launching" | "error"

function trackLaunchResult(
  labSlug: string,
  result: LaunchResult,
  provisioningMs: number
): void {
  switch (result.kind) {
    case "denied":
      track("session_launch_denied", { lab_slug: labSlug, code: result.code })
      break
    case "session":
      track("session_launched", {
        lab_slug: labSlug,
        session_id: result.session.sessionId,
        provisioning_ms: provisioningMs,
      })
      break
    case "queued":
      track("session_queued", {
        lab_slug: labSlug,
        position: result.queued.position,
        eta_sec: result.queued.etaSec,
      })
      break
  }
}

function toLaunchStatus(mutationStatus: string): LaunchStatus {
  switch (mutationStatus) {
    case "pending":
      return "launching"
    case "error":
      return "error"
    default:
      return "idle"
  }
}

/**
 * Launches a lab and reports the outcome through `onResult`. The outcome is an
 * event, not derived state, so the caller reacts to it in a callback rather
 * than in an effect watching the last result.
 */
export function useLaunchLab(
  labSlug: string,
  onResult: (result: LaunchResult) => void
) {
  const launchMutation = useMutation({
    mutationFn: async () => {
      const startedAt = Date.now()
      const result = await launchLab(labSlug)
      return { result, provisioningMs: Date.now() - startedAt }
    },
    onSuccess: ({ result, provisioningMs }) => {
      trackLaunchResult(labSlug, result, provisioningMs)
      onResult(result)
    },
    onError: (error) => {
      toast.error(error.message)
      track("session_launch_failed", {
        lab_slug: labSlug,
        error: error.message,
      })
    },
  })

  return {
    status: toLaunchStatus(launchMutation.status),
    error: launchMutation.error?.message ?? null,
    launch: launchMutation.mutate,
    reset: launchMutation.reset,
  }
}
