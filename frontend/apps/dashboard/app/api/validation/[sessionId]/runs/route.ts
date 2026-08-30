import { serverEnv } from "@repo/api/env"
import { getRequestLocale } from "@repo/api/request-locale"
import { getBackendToken } from "@repo/auth/server"

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
    `${serverEnv.BACKEND_URL}/sessions/${sessionId}/validation-runs`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Locale": await getRequestLocale(),
      },
      cache: "no-store",
    }
  )
  if (!upstream.ok) {
    return new Response(await upstream.text(), { status: upstream.status })
  }
  const wire = (await upstream.json()) as RunListItemWire[]
  const runs = wire.map((run) => ({
    id: run.id,
    labSlug: run.lab_slug,
    status: run.status,
    startedAt: run.started_at,
    finishedAt: run.finished_at,
    durationMs: run.duration_ms,
    passedChecks: run.passed_checks,
    totalChecks: run.total_checks,
  }))
  return Response.json(runs)
}
