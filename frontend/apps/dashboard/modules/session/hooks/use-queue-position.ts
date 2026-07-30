"use client"

import { useQuery } from "@tanstack/react-query"
import { type QueueStatusShape, queueStatusQuery } from "../query"

export type { QueueStatusShape }

export function useQueuePosition(
  labSlug: string | null
): QueueStatusShape | null {
  const { data } = useQuery({
    ...queueStatusQuery(labSlug ?? ""),
    enabled: !!labSlug,
  })
  return data ?? null
}
