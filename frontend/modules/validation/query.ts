import { queryOptions } from "@tanstack/react-query"
import { fetchValidationRunDetail, fetchValidationRuns } from "./api"

export const validationKeys = {
  all: ["validation"] as const,
  runs: (sessionId: string) =>
    [...validationKeys.all, "runs", sessionId] as const,
  run: (sessionId: string, runId: string) =>
    [...validationKeys.all, "run", sessionId, runId] as const,
}

export function validationRunsQuery(sessionId: string) {
  return queryOptions({
    queryKey: validationKeys.runs(sessionId),
    queryFn: () => fetchValidationRuns(sessionId),
    enabled: !!sessionId,
  })
}

export function validationRunQuery(sessionId: string, runId: string | null) {
  return queryOptions({
    queryKey: validationKeys.run(sessionId, runId ?? ""),
    queryFn: () => fetchValidationRunDetail(sessionId, runId as string),
    enabled: !!sessionId && !!runId,
  })
}
