"use client"

import { useState, useTransition } from "react"
import { toast } from "sonner"
import type { LaunchResult } from "../types"
import { launchLab } from "../actions"
import { track } from "@/lib/analytics"

export type LaunchStatus = "idle" | "launching" | "error"

export function useLaunchLab(labSlug: string) {
  const [pending, startTransition] = useTransition()
  const [result, setResult] = useState<LaunchResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  function launch() {
    setError(null)
    const launchStartedAt = Date.now()
    startTransition(async () => {
      try {
        const res = await launchLab(labSlug)
        setResult(res)
        if (res.kind === "session") {
          track("session_launched", {
            lab_slug: labSlug,
            session_id: res.session.sessionId,
            provisioning_ms: Date.now() - launchStartedAt,
          })
        } else {
          track("session_queued", {
            lab_slug: labSlug,
            position: res.queued.position,
            eta_sec: res.queued.etaSec,
          })
        }
      } catch (e) {
        const msg = (e as Error).message
        setError(msg)
        toast.error(msg)
        track("session_launch_failed", { lab_slug: labSlug, error: msg })
      }
    })
  }

  function reset() {
    setResult(null)
    setError(null)
  }

  const status: LaunchStatus = pending ? "launching" : error ? "error" : "idle"

  return { status, result, error, launch, reset }
}
