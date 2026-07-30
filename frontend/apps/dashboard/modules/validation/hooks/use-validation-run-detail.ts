"use client"

import { useQuery } from "@tanstack/react-query"
import { validationRunQuery } from "../query"

export function useValidationRunDetail(
  sessionId: string,
  runId: string | null
) {
  const query = useQuery(validationRunQuery(sessionId, runId))
  return {
    detail: query.data ?? null,
    isLoading: query.isLoading && !!runId,
  }
}
