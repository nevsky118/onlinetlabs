import type { ChatHistoryMessage, SessionSummary } from "./types"
import { mapSessionSummaryList } from "./lib/mappings"

export async function fetchChatHistory(
  sessionId: string,
  signal?: AbortSignal
): Promise<ChatHistoryMessage[]> {
  const r = await fetch(`/api/chat/history/${sessionId}`, { signal })
  if (!r.ok) return []
  return r.json()
}

export async function fetchChatSessions(
  signal?: AbortSignal
): Promise<SessionSummary[]> {
  const r = await fetch("/api/chat/sessions", { signal })
  if (!r.ok) return []
  return mapSessionSummaryList(await r.json())
}
