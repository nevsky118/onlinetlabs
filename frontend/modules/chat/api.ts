import type {
  AgentActivityEvent,
  ChatHistoryMessage,
  ChatModelsResponse,
  SessionSummary,
} from "./types"
import { mapAgentActivityEvent, mapSessionSummaryList } from "./lib/mappings"
import { clientEnv } from "@/lib/env.client"

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
  const r = await fetch(url.toString(), { signal })
  if (!r.ok) return []
  const data: unknown[] = await r.json()
  return data.map(mapAgentActivityEvent)
}
