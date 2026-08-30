import type { ModelOption } from "./types"

type ModelWire = Record<string, unknown>

function mapModel(wire: ModelWire): ModelOption {
  return {
    id: String(wire.id),
    label: String(wire.label ?? wire.name ?? wire.id),
  }
}

export async function fetchChatModels(): Promise<ModelOption[]> {
  const response = await fetch("/api/chat/models", { cache: "no-store" })
  if (!response.ok) return []
  const payload = await response.json()
  const rows: ModelWire[] = Array.isArray(payload)
    ? payload
    : ((payload?.models ?? []) as ModelWire[])
  return rows.map(mapModel)
}

/** The saved choice comes from the server, the source of truth, not localStorage. */
export async function fetchDefaultModelId(): Promise<string | null> {
  const response = await fetch("/api/users/preferences", { cache: "no-store" })
  if (!response.ok) return null
  const payload = await response.json()
  return payload?.default_model_id ? String(payload.default_model_id) : null
}

export async function saveDefaultModelId(modelId: string): Promise<void> {
  const response = await fetch("/api/users/preferences", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ default_model_id: modelId }),
  })
  if (!response.ok) throw new Error(`saveDefaultModelId ${response.status}`)
}

export async function fetchActiveSessionCount(): Promise<number | null> {
  const response = await fetch("/api/users/sessions", { cache: "no-store" })
  if (!response.ok) return null
  const payload = await response.json()
  return typeof payload?.count === "number" ? payload.count : null
}

export async function revokeOtherSessions(): Promise<void> {
  await fetch("/api/users/sessions", { method: "DELETE" })
}
