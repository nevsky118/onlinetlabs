import type { UIMessage } from "@ai-sdk/react"

export function getDomainLabel(labSlug: string): {
  domain: string
  name: string
} {
  if (labSlug.includes("docker") || labSlug.includes("container")) {
    return { domain: "Docker", name: labSlug }
  }
  if (labSlug.includes("postgres") || labSlug.includes("sql")) {
    return { domain: "PostgreSQL", name: labSlug }
  }
  return { domain: "GNS3", name: labSlug }
}

export function mapToUIMessage(message: {
  id: string
  role: string
  parts: unknown[]
  created_at?: string
}): UIMessage {
  // created_at goes into metadata, needed to embed logs into the flow by time.
  return {
    id: message.id,
    role: message.role as "user" | "assistant",
    parts: message.parts as UIMessage["parts"],
    ...(message.created_at
      ? { metadata: { createdAt: message.created_at } }
      : {}),
  } as UIMessage
}
