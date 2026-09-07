"use client"

import { useEffect, useRef, useState } from "react"
import type { LaunchDenial, QueuedResult, SessionData } from "../types"
import { fetchQueueStatus, launchLab } from "../actions"

export const QUEUE_POLL_INTERVAL_MS = 5000

// Minimum gap between launch attempts.
const QUEUE_CLAIM_INTERVAL_MS = 15000

// Watches the queue position and claims a slot once one frees.
export function useQueuePoll({
  labSlug,
  initial,
  enabled,
  onReady,
  onDenied,
}: {
  labSlug: string
  initial: QueuedResult
  enabled: boolean
  onReady: (session: SessionData) => void
  onDenied: (denial: LaunchDenial) => void
}): QueuedResult {
  const [queued, setQueued] = useState(initial)
  const lastClaimAt = useRef(0)

  useEffect(() => {
    if (!enabled) return
    let active = true

    const poll = async () => {
      try {
        const status = await fetchQueueStatus(labSlug)
        if (!active) return
        if (status.in_queue) {
          setQueued((current) => ({
            ...current,
            position: status.queue_position ?? current.position,
            depth: status.queue_depth,
            etaSec: status.eta_sec ?? current.etaSec,
          }))
        }
        // Claim on a free slot, or when the place has expired.
        const worthClaiming = status.slot_available || !status.in_queue
        const claimAllowed =
          Date.now() - lastClaimAt.current >= QUEUE_CLAIM_INTERVAL_MS
        if (!worthClaiming || !claimAllowed) return

        lastClaimAt.current = Date.now()
        const result = await launchLab(labSlug)
        if (!active) return
        switch (result.kind) {
          case "session":
            onReady(result.session)
            break
          case "queued":
            setQueued(result.queued)
            break
          case "denied":
            onDenied(result)
            break
        }
      } catch {
        // A failed probe is not fatal: retry on the next tick.
      }
    }

    const intervalId = setInterval(poll, QUEUE_POLL_INTERVAL_MS)
    return () => {
      active = false
      clearInterval(intervalId)
    }
  }, [enabled, labSlug, onReady, onDenied])

  return queued
}
