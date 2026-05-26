"use client"

import { useCallback, useEffect, useState } from "react"

export type ValidationRunListItem = {
  id: string
  labSlug: string
  status: "running" | "passed" | "failed" | "error"
  durationMs: number | null
  passedChecks: number | null
  totalChecks: number | null
  startedAt: string
  finishedAt: string | null
}

type Result = {
  runs: ValidationRunListItem[]
  isLoading: boolean
  mutate: () => Promise<void>
}

export function useValidationRuns(sessionId: string): Result {
  const [runs, setRuns] = useState<ValidationRunListItem[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await fetch(`/api/validation/${sessionId}/runs`, {
        cache: "no-store",
      })
      if (!res.ok) return
      const data = (await res.json()) as ValidationRunListItem[]
      setRuns(data)
    } catch {
      // swallow — UI keeps previous state
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    if (!sessionId) return
    void load()
  }, [sessionId, load])

  return { runs, isLoading, mutate: load }
}
