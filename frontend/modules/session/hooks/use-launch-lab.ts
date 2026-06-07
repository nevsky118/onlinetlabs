"use client"

import { useMutation } from "@tanstack/react-query"
import { toast } from "sonner"
import type { LaunchResult } from "../types"
import { launchLab } from "../actions"
import { track } from "@/lib/analytics"

export type LaunchStatus = "idle" | "launching" | "error"

export function useLaunchLab(labSlug: string) {
  const m = useMutation({
    mutationFn: async () => {
      const startedAt = Date.now()
      const res = await launchLab(labSlug)
      return { res, startedAt }
    },
    onSuccess: ({ res, startedAt }) => {
      if (res.kind === "session") {
        track("session_launched", {
          lab_slug: labSlug,
          session_id: res.session.sessionId,
          provisioning_ms: Date.now() - startedAt,
        })
      } else {
        track("session_queued", {
          lab_slug: labSlug,
          position: res.queued.position,
          eta_sec: res.queued.etaSec,
        })
      }
    },
    onError: (e) => {
      const msg = (e as Error).message
      toast.error(msg)
      track("session_launch_failed", { lab_slug: labSlug, error: msg })
    },
  })

  const status: LaunchStatus = m.isPending
    ? "launching"
    : m.isError
      ? "error"
      : "idle"

  const result: LaunchResult | null = m.data?.res ?? null

  return {
    status,
    result,
    error: m.error ? (m.error as Error).message : null,
    launch: () => m.mutate(),
    reset: m.reset,
  }
}
