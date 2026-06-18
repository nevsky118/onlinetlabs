import type {
  ChatHistoryMessage,
  ChatModelsResponse,
  SessionSummary,
} from "./types"
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

export async function fetchChatModels(
  signal?: AbortSignal
): Promise<ChatModelsResponse> {
  const r = await fetch("/api/chat/models", { signal })
  if (!r.ok) return { canSelect: false, defaultModelId: "", models: [] }
  const d = await r.json()
  return {
    canSelect: !!d.can_select,
    defaultModelId: d.default_model_id ?? "",
    models: d.models ?? [],
  }
}
