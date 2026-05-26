"use client"

import { useEffect, useState } from "react"

export type ValidationCheck = {
  kind: string
  params: Record<string, unknown>
  ok: boolean
  expected: Record<string, unknown>
  actual: Record<string, unknown>
  log?: string
}

export type ValidationStep = {
  id: string
  title: string
  ok: boolean
  checks: ValidationCheck[]
}

export type ValidationRunDetail = {
  id: string
  labSlug: string
  status: "running" | "passed" | "failed" | "error"
  steps: ValidationStep[]
  startedAt: string
  finishedAt: string | null
}

type Result = {
  detail: ValidationRunDetail | null
  isLoading: boolean
}

export function useValidationRunDetail(
  sessionId: string,
  runId: string | null
): Result {
  const [detail, setDetail] = useState<ValidationRunDetail | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)

  useEffect(() => {
    if (!sessionId || !runId) {
      setDetail(null)
      return
    }
    let alive = true
    setIsLoading(true)
    ;(async () => {
      try {
        const res = await fetch(`/api/validation/${sessionId}/runs/${runId}`, {
          cache: "no-store",
        })
        if (!res.ok) return
        const data = (await res.json()) as ValidationRunDetail
        if (!alive) return
        setDetail(data)
      } catch {
        // swallow
      } finally {
        if (alive) setIsLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [sessionId, runId])

  return { detail, isLoading }
}
