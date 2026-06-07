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

export type ValidationStreamEvent =
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
