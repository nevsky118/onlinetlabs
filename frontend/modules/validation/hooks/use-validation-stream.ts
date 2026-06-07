"use client"

import { useQueryClient } from "@tanstack/react-query"
import { useCallback, useRef, useState } from "react"
import type {
  ValidationCheck,
  ValidationStep,
  ValidationStreamEvent,
} from "../types"
import { startValidationStream } from "../api"
import { validationKeys } from "../query"

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

const INITIAL_STATE: ValidationStreamState = {
  status: "idle",
  currentRunId: null,
  steps: [],
}

function applyEvent(
  state: ValidationStreamState,
  ev: ValidationStreamEvent
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

function parseSSEBuffer(buffer: string): {
  events: ValidationStreamEvent[]
  rest: string
} {
  const events: ValidationStreamEvent[] = []
  let rest = buffer
  let idx = rest.indexOf("\n\n")
  while (idx !== -1) {
    const chunk = rest.slice(0, idx)
    rest = rest.slice(idx + 2)
    const lines = chunk.split("\n")
    for (const line of lines) {
      if (!line.startsWith("data:")) continue
      const payload = line.slice(5).trim()
      if (!payload) continue
      try {
        events.push(JSON.parse(payload) as ValidationStreamEvent)
      } catch {
        // ignore malformed frame
      }
    }
    idx = rest.indexOf("\n\n")
  }
  return { events, rest }
}

export function useValidationStream(sessionId: string) {
  const [state, setState] = useState<ValidationStreamState>(INITIAL_STATE)
  const abortRef = useRef<AbortController | null>(null)
  const qc = useQueryClient()

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
          const res = await startValidationStream(sessionId, slug, ac.signal)
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
              if (events.some((ev) => ev.type === "run.finish")) {
                qc.invalidateQueries({
                  queryKey: validationKeys.runs(sessionId),
                })
              }
            }
          }
        } catch (e) {
          if ((e as Error).name === "AbortError") return
          setState((s) => ({ ...s, status: "error" }))
        }
      })()
    },
    [sessionId, stop, qc]
  )

  return { state, start, stop }
}
