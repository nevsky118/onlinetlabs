"use client"

import { useCallback, useRef, useState } from "react"
import type {
  ValidationCheck,
  ValidationStep,
} from "./use-validation-run-detail"

export type ValidationStreamStatus =
  | "idle"
  | "running"
  | "passed"
  | "failed"
  | "error"

export type ValidationStreamState = {
  status: ValidationStreamStatus
  currentRunId: string | null
  steps: ValidationStep[]
}

type SSEEvent =
  | { type: "run.start"; totalSteps: number; runId: string }
  | {
      type: "step.start"
      stepId: string
      title: string
      totalChecks: number
    }
  | {
      type: "check.start"
      stepId: string
      checkIndex: number
      kind: string
      params: Record<string, unknown>
    }
  | { type: "check.log"; stepId: string; line: string }
  | {
      type: "check.result"
      stepId: string
      checkIndex: number
      ok: boolean
      expected: Record<string, unknown>
      actual: Record<string, unknown>
    }
  | { type: "step.result"; stepId: string; title: string; ok: boolean }
  | { type: "run.finish"; ok: boolean; runId: string }

const INITIAL_STATE: ValidationStreamState = {
  status: "idle",
  currentRunId: null,
  steps: [],
}

function applyEvent(
  state: ValidationStreamState,
  ev: SSEEvent
): ValidationStreamState {
  switch (ev.type) {
    case "run.start":
      return { status: "running", currentRunId: ev.runId, steps: [] }
    case "step.start": {
      const step: ValidationStep = {
        id: ev.stepId,
        title: ev.title,
        ok: false,
        checks: [],
      }
      return { ...state, steps: [...state.steps, step] }
    }
    case "check.start": {
      const check: ValidationCheck = {
        kind: ev.kind,
        params: ev.params,
        ok: false,
        expected: {},
        actual: {},
      }
      const steps = state.steps.map((s) =>
        s.id === ev.stepId ? { ...s, checks: [...s.checks, check] } : s
      )
      return { ...state, steps }
    }
    case "check.log": {
      const steps = state.steps.map((s) => {
        if (s.id !== ev.stepId) return s
        const checks = s.checks.slice()
        const last = checks.length - 1
        if (last < 0) return s
        const c = checks[last]
        const prev = c.log ?? ""
        checks[last] = { ...c, log: prev + ev.line + "\n" }
        return { ...s, checks }
      })
      return { ...state, steps }
    }
    case "check.result": {
      const steps = state.steps.map((s) => {
        if (s.id !== ev.stepId) return s
        const checks = s.checks.map((c, i) =>
          i === ev.checkIndex
            ? { ...c, ok: ev.ok, expected: ev.expected, actual: ev.actual }
            : c
        )
        return { ...s, checks }
      })
      return { ...state, steps }
    }
    case "step.result": {
      const steps = state.steps.map((s) =>
        s.id === ev.stepId ? { ...s, ok: ev.ok } : s
      )
      return { ...state, steps }
    }
    case "run.finish":
      return { ...state, status: ev.ok ? "passed" : "failed" }
    default:
      return state
  }
}

function parseSSEBuffer(buffer: string): { events: SSEEvent[]; rest: string } {
  const events: SSEEvent[] = []
  let rest = buffer
  let idx: number
  while ((idx = rest.indexOf("\n\n")) !== -1) {
    const chunk = rest.slice(0, idx)
    rest = rest.slice(idx + 2)
    const lines = chunk.split("\n")
    for (const line of lines) {
      if (!line.startsWith("data:")) continue
      const payload = line.slice(5).trim()
      if (!payload) continue
      try {
        events.push(JSON.parse(payload) as SSEEvent)
      } catch {
        // ignore malformed frame
      }
    }
  }
  return { events, rest }
}

export function useValidationStream(sessionId: string) {
  const [state, setState] = useState<ValidationStreamState>(INITIAL_STATE)
  const abortRef = useRef<AbortController | null>(null)

  const stop = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
  }, [])

  const start = useCallback(
    (slug: string) => {
      stop()
      setState({ status: "running", currentRunId: null, steps: [] })

      const ac = new AbortController()
      abortRef.current = ac

      ;(async () => {
        try {
          const res = await fetch(`/api/validation/${sessionId}/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ slug }),
            signal: ac.signal,
          })
          if (!res.ok || !res.body) {
            setState((s) => ({ ...s, status: "error" }))
            return
          }
          const reader = res.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ""
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })
            const { events, rest } = parseSSEBuffer(buffer)
            buffer = rest
            if (events.length > 0) {
              setState((prev) => events.reduce(applyEvent, prev))
            }
          }
        } catch (e) {
          if ((e as Error).name === "AbortError") return
          setState((s) => ({ ...s, status: "error" }))
        }
      })()
    },
    [sessionId, stop]
  )

  return { state, start, stop }
}
