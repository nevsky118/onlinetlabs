import type { AgentActivityEvent, SessionSummary } from "../types"

type SessionSummaryWire = {
  id: string
  lab_slug: string
  started_at: string
  status: string
}

export function mapSessionSummary(wire: SessionSummaryWire): SessionSummary {
  return {
    id: wire.id,
    labSlug: wire.lab_slug,
    startedAt: wire.started_at,
    status: wire.status,
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

export function mapAgentActivityEvent(raw: unknown): AgentActivityEvent {
  const wire = raw as AgentActivityEventWire
  return {
    id: wire.id,
    sessionId: wire.session_id,
    userId: wire.user_id,
    ts: wire.ts,
    source: wire.source,
    kind: wire.kind,
    agent: wire.agent ?? null,
    severity: wire.severity,
    summary: wire.summary,
    detail: wire.detail ?? null,
  }
}

export function mapSessionSummaryList(
  arr: SessionSummaryWire[]
): SessionSummary[] {
  return arr.map(mapSessionSummary)
}
