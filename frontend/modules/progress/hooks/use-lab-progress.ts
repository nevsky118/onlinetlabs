"use client"

import { useQuery } from "@tanstack/react-query"
import { labProgressQuery } from "../query"

export function useLabProgress(labSlug: string) {
  const { data, refetch } = useQuery(labProgressQuery(labSlug))
  return { progress: data ?? null, refresh: refetch }
}
