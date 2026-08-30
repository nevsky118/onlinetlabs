"use client"

import { useEffect, useState } from "react"
import type { QueuedResult, SessionData } from "../types"
import { launchLab } from "../actions"

export const QUEUE_POLL_INTERVAL_MS = 5000

/**
 * Re-attempts the launch on an interval while the user waits in the queue and
 * reports the granted session through `onReady`. Returns the freshest queue
 * position so the dialog stays a pure view.
 */
export function useQueuePoll({
  labSlug,
  initial,
  enabled,
  onReady,
}: {
  labSlug: string
  initial: QueuedResult
  enabled: boolean
  onReady: (session: SessionData) => void
}): QueuedResult {
  const [queued, setQueued] = useState(initial)

  useEffect(() => {
    if (!enabled) return
    let active = true

    const poll = async () => {
      try {
        const result = await launchLab(labSlug)
        if (!active) return
        switch (result.kind) {
          case "session":
            onReady(result.session)
            break
          case "queued":
            setQueued(result.queued)
            break
          default:
            break
        }
      } catch {
        // A failed probe is not fatal: keep the user in the queue and retry.
      }
    }

    const intervalId = setInterval(poll, QUEUE_POLL_INTERVAL_MS)
    return () => {
      active = false
      clearInterval(intervalId)
    }
  }, [enabled, labSlug, onReady])

  return queued
}
