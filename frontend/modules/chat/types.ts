export interface ChatHistoryMessage {
  id: string
  role: string
  parts: unknown[]
  created_at?: string
}

export interface SessionSummary {
  id: string
  labSlug: string
  startedAt: string
  status: string
}

export type ChatModelsResponse = {
  canSelect: boolean
  defaultModelId: string
  models: { id: string; label: string }[]
}

export interface AgentActivityEvent {
  id: string
  sessionId: string
  userId: string
  ts: string
  source: string
  kind: string
  agent: string | null
  severity: string
  summary: string
  detail: Record<string, unknown> | null
}
