import { clientEnv } from "@repo/api/env.client"
import type {
  AgentActivityEvent,
  ChatHistoryMessage,
  ChatModelsResponse,
  SessionSummary,
} from "./types"
import { mapAgentActivityEvent, mapSessionSummaryList } from "./lib/mappings"

export async function fetchChatHistory(
  sessionId: string,
  signal?: AbortSignal
): Promise<ChatHistoryMessage[]> {
  const response = await fetch(`/api/chat/history/${sessionId}`, { signal })
  if (!response.ok) return []
  return response.json()
}

export async function fetchChatSessions(
  signal?: AbortSignal
): Promise<SessionSummary[]> {
  const response = await fetch("/api/chat/sessions", { signal })
  if (!response.ok) return []
  return mapSessionSummaryList(await response.json())
}

export async function fetchChatModels(
  signal?: AbortSignal
): Promise<ChatModelsResponse> {
  const response = await fetch("/api/chat/models", { signal })
  if (!response.ok) return { canSelect: false, defaultModelId: "", models: [] }
  const payload = await response.json()
  return {
    canSelect: !!payload.can_select,
    defaultModelId: payload.default_model_id ?? "",
    models: payload.models ?? [],
  }
}

export async function fetchAgentActivity(
  sessionId: string,
  since?: string,
  signal?: AbortSignal
): Promise<AgentActivityEvent[]> {
  const url = new URL(
    `/api/chat/agent-activity/${sessionId}`,
    typeof window !== "undefined"
      ? window.location.origin
      : clientEnv.NEXT_PUBLIC_APP_URL
  )
  if (since) url.searchParams.set("since", since)
  const response = await fetch(url.toString(), { signal })
  if (!response.ok) return []
  const data: unknown[] = await response.json()
  return data.map(mapAgentActivityEvent)
}
