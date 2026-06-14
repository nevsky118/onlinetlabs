"use server"

import type { LabProgress } from "./types"
import { getLabProgressApi } from "./api"

export async function fetchLabProgress(
  labSlug: string
): Promise<LabProgress | null> {
  const res = await getLabProgressApi(labSlug)
  // 404 — прогресса по лабе ещё нет; 401 — нет сессии. И то и другое = «нет данных».
  if (res.status === 404 || res.status === 401) return null
  if (!res.ok) throw new Error(`fetchLabProgress ${res.status}`)
  const d = await res.json()
  return {
    labSlug: d.lab_slug,
    status: d.status,
    score: d.score,
    currentStep: d.current_step,
    startedAt: d.started_at,
    completedAt: d.completed_at,
  }
}
