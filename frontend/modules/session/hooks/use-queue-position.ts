"use client"

import { useEffect, useState } from "react"
import { fetchQueueStatus } from "../actions"

export type QueueStatusShape = {
  inQueue: boolean
  position: number
  depth: number
  etaSec: number
}

export function useQueuePosition(
  labSlug: string | null
): QueueStatusShape | null {
  const [status, setStatus] = useState<QueueStatusShape | null>(null)

  useEffect(() => {
    if (!labSlug) return
    let alive = true

    const tick = async () => {
      try {
        const d = await fetchQueueStatus(labSlug)
        if (!alive) return
        setStatus({
          inQueue: d.in_queue,
          position: d.queue_position ?? 0,
          depth: d.queue_depth ?? 0,
          etaSec: d.eta_sec ?? 0,
        })
      } catch {
        // swallow — interval keeps trying
      }
    }

    tick()
    const id = setInterval(tick, 5000)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [labSlug])

  return status
}
