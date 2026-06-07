import type { SessionSummary } from "../types"

type SessionSummaryWire = {
  id: string
  lab_slug: string
  started_at: string
  status: string
}

export function mapSessionSummary(w: SessionSummaryWire): SessionSummary {
  return {
    id: w.id,
    labSlug: w.lab_slug,
    startedAt: w.started_at,
    status: w.status,
  }
}

export function mapSessionSummaryList(
  arr: SessionSummaryWire[]
): SessionSummary[] {
  return arr.map(mapSessionSummary)
}
