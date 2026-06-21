import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

type CheckWire = {
  kind: string
  params: Record<string, unknown>
  ok: boolean
  expected: Record<string, unknown>
  actual: Record<string, unknown>
  log?: string
}

type StepWire = {
  id: string
  title: string
  ok: boolean
  checks: CheckWire[]
}

type RunDetailWire = {
  id: string
  lab_slug: string
  status: string
  steps: StepWire[]
  started_at: string
  finished_at: string | null
}

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ sessionId: string; runId: string }> }
) {
  const { sessionId, runId } = await ctx.params
  const token = await getBackendToken()
  if (!token) return new Response("Unauthorized", { status: 401 })

  const upstream = await fetch(
    `${serverEnv.BACKEND_URL}/sessions/${sessionId}/validation-runs/${runId}`,
    {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    }
  )
  if (!upstream.ok) {
    return new Response(await upstream.text(), { status: upstream.status })
  }
  const w = (await upstream.json()) as RunDetailWire
  const detail = {
    id: w.id,
    labSlug: w.lab_slug,
    status: w.status,
    steps: w.steps ?? [],
    startedAt: w.started_at,
    finishedAt: w.finished_at,
  }
  return Response.json(detail)
}
