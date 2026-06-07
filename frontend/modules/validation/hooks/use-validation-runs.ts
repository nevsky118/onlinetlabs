"use client"

import { useQuery } from "@tanstack/react-query"
import { validationRunsQuery } from "../query"

export function useValidationRuns(sessionId: string) {
  const query = useQuery(validationRunsQuery(sessionId))
  return {
    runs: query.data ?? [],
    isLoading: query.isLoading,
    mutate: () => query.refetch(),
  }
}
