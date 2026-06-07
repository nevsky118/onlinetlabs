export interface ChatHistoryMessage {
  id: string
  role: string
  parts: unknown[]
}

export interface SessionSummary {
  id: string
  labSlug: string
  startedAt: string
  status: string
}
