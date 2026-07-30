import type { ValidationRunDetail, ValidationRunListItem } from "./types"

export async function fetchValidationRuns(
  sessionId: string
): Promise<ValidationRunListItem[]> {
  const r = await fetch(`/api/validation/${sessionId}/runs`, {
    cache: "no-store",
  })
  if (!r.ok) throw new Error("runs fetch failed")
  return r.json()
}

export async function fetchValidationRunDetail(
  sessionId: string,
  runId: string
): Promise<ValidationRunDetail> {
  const r = await fetch(`/api/validation/${sessionId}/runs/${runId}`, {
    cache: "no-store",
  })
  if (!r.ok) throw new Error("run detail fetch failed")
  return r.json()
}

export async function startValidationStream(
  sessionId: string,
  labSlug: string,
  signal?: AbortSignal
): Promise<Response> {
  return fetch(`/api/validation/${sessionId}/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slug: labSlug }),
    signal,
  })
}
