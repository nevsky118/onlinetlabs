"use server"

import type { LabProgress } from "./types"
import { getLabProgressApi } from "./api"

export async function fetchLabProgress(
  labSlug: string
): Promise<LabProgress | null> {
  const res = await getLabProgressApi(labSlug)
  // 404 means there is no lab progress yet; 401 means there is no session. Both are equivalent to "no data".
  if (res.status === 404 || res.status === 401) return null
  if (!res.ok) throw new Error(`fetchLabProgress ${res.status}`)
  const payload = await res.json()
  return {
    labSlug: payload.lab_slug,
    status: payload.status,
    score: payload.score,
    currentStep: payload.current_step,
    startedAt: payload.started_at,
    completedAt: payload.completed_at,
  }
}
