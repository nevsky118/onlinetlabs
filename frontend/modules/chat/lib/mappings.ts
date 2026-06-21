import type { AgentActivityEvent, SessionSummary } from "../types"

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

type AgentActivityEventWire = {
  id: string
  session_id: string
  user_id: string
  ts: string
  source: string
  kind: string
  agent: string | null
  severity: string
  summary: string
  detail: Record<string, unknown> | null
}

export function mapAgentActivityEvent(w: unknown): AgentActivityEvent {
  const e = w as AgentActivityEventWire
  return {
    id: e.id,
    sessionId: e.session_id,
    userId: e.user_id,
    ts: e.ts,
    source: e.source,
    kind: e.kind,
    agent: e.agent ?? null,
    severity: e.severity,
    summary: e.summary,
    detail: e.detail ?? null,
  }
}

export function mapSessionSummaryList(
  arr: SessionSummaryWire[]
): SessionSummary[] {
  return arr.map(mapSessionSummary)
}
