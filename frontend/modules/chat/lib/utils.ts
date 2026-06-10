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

export function mapToUIMessage(m: {
  id: string
  role: string
  parts: unknown[]
}): UIMessage {
  return {
    id: m.id,
    role: m.role as "user" | "assistant",
    parts: m.parts as UIMessage["parts"],
  }
}
