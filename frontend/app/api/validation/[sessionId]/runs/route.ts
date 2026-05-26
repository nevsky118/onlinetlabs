import { getBackendToken } from "@/auth/token"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

type RunListItemWire = {
  id: string
  lab_slug: string
  status: string
  started_at: string
  finished_at: string | null
  duration_ms: number | null
  passed_checks: number | null
  total_checks: number | null
}

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ sessionId: string }> }
) {
  const { sessionId } = await ctx.params
  const token = await getBackendToken()
  if (!token) return new Response("Unauthorized", { status: 401 })

  const upstream = await fetch(
    `${BACKEND_URL}/sessions/${sessionId}/validation-runs`,
    {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    }
  )
  if (!upstream.ok) {
    return new Response(await upstream.text(), { status: upstream.status })
  }
  const wire = (await upstream.json()) as RunListItemWire[]
  const runs = wire.map((w) => ({
    id: w.id,
    labSlug: w.lab_slug,
    status: w.status,
    startedAt: w.started_at,
    finishedAt: w.finished_at,
    durationMs: w.duration_ms,
    passedChecks: w.passed_checks,
    totalChecks: w.total_checks,
  }))
  return Response.json(runs)
}
