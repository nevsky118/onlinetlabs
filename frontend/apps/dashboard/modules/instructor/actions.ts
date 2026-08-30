"use server"

import type {
  Autonomy,
  CohortCell,
  CohortMetrics,
  OrgEffect,
  StudentDetail,
  StudentsOverview,
  TimelineItem,
  TimeToCompetence,
} from "./types"
import {
  getCohortMetricsApi,
  getSessionTimelineApi,
  getStudentDetailApi,
  getStudentsOverviewApi,
} from "./api"

export async function fetchStudentsOverview(): Promise<StudentsOverview> {
  const res = await getStudentsOverviewApi()
  if (!res.ok) throw new Error(`fetchStudentsOverview ${res.status}`)
  const payload = await res.json()
  return {
    students: (payload.students ?? []).map(mapStudentOverview),
    totalStudents: payload.total_students,
    totalHints: payload.total_hints,
  }
}

export async function fetchStudentDetail(
  userId: string
): Promise<StudentDetail | null> {
  const res = await getStudentDetailApi(userId)
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`fetchStudentDetail ${res.status}`)
  const payload = await res.json()
  return {
    userId: payload.user_id,
    name: payload.name,
    email: payload.email,
    role: payload.role,
    labsCompleted: payload.labs_completed,
    labsInProgress: payload.labs_in_progress,
    avgScore: payload.avg_score,
    totalHints: payload.total_hints,
    totalSessions: payload.total_sessions,
    labs: (payload.labs ?? []).map((lab: Record<string, unknown>) => ({
      labSlug: lab.lab_slug,
      labTitle: lab.lab_title,
      status: lab.status,
      score: lab.score,
      currentStep: lab.current_step,
      hints: lab.hints,
      sessions: lab.sessions,
      attempts: lab.attempts,
      startedAt: lab.started_at,
      completedAt: lab.completed_at,
      lastActiveAt: lab.last_active_at,
    })),
    sessions: (payload.sessions ?? []).map(
      (session: Record<string, unknown>) => ({
        sessionId: session.session_id,
        labSlug: session.lab_slug,
        labTitle: session.lab_title,
        status: session.status,
        startedAt: session.started_at,
        endedAt: session.ended_at,
        messageCount: session.message_count,
        hintCount: session.hint_count,
      })
    ),
  }
}

export async function fetchSessionTimeline(
  userId: string,
  sessionId: string
): Promise<TimelineItem[]> {
  const res = await getSessionTimelineApi(userId, sessionId)
  if (!res.ok) throw new Error(`fetchSessionTimeline ${res.status}`)
  const rows = (await res.json()) as Record<string, unknown>[]
  return rows.map((row) => ({
    kind: row.kind as TimelineItem["kind"],
    ts: row.ts as string,
    parts: (row.parts as TimelineItem["parts"]) ?? null,
    text: (row.text as string) ?? null,
    action: (row.action as string) ?? null,
    severity: (row.severity as string) ?? null,
    hintLevel: (row.hint_level as number) ?? null,
    struggleType: (row.struggle_type as string) ?? null,
  }))
}

export async function fetchCohortMetrics(
  byArm = false
): Promise<CohortMetrics> {
  const res = await getCohortMetricsApi(byArm)
  if (!res.ok) throw new Error(`fetchCohortMetrics ${res.status}`)
  const payload = await res.json()
  return {
    bySkill: (payload.by_skill ?? []).map(mapCohortCell),
    pooled: mapCohortCell(payload.pooled),
    byArm: payload.by_arm
      ? (payload.by_arm as Record<string, unknown>[]).map(mapCohortCell)
      : null,
    headlineArm: (payload.headline_arm as string) ?? null,
  }
}

function mapTimeToCompetence(t: Record<string, unknown>): TimeToCompetence {
  return {
    medianCalendarSeconds: (t.median_calendar_seconds as number) ?? null,
    medianActiveSeconds: (t.median_active_seconds as number) ?? null,
    reachRate: (t.reach_rate as number) ?? null,
    reachRateAtHorizon: (t.reach_rate_at_horizon as number) ?? null,
    restrictedMeanCalendarSeconds:
      (t.restricted_mean_calendar_seconds as number) ?? null,
    n: (t.n as number) ?? 0,
    censored: (t.censored as number) ?? 0,
  }
}

function mapAutonomy(wire: Record<string, unknown>): Autonomy {
  return {
    meanL1Interventions: (wire.mean_l1_interventions as number) ?? null,
    meanL2Interventions: (wire.mean_l2_interventions as number) ?? null,
    meanSessionsToL2: (wire.mean_sessions_to_l2 as number) ?? null,
  }
}

function mapOrgEffect(wire: Record<string, unknown>): OrgEffect {
  return {
    l1EscalationsMean: (wire.l1_escalations_mean as number) ?? null,
    l2EscalationsMean: (wire.l2_escalations_mean as number) ?? null,
    l1RepeatedErrorsMean: (wire.l1_repeated_errors_mean as number) ?? null,
    l2RepeatedErrorsMean: (wire.l2_repeated_errors_mean as number) ?? null,
    note: (wire.note as string) ?? null,
  }
}

function mapCohortCell(wire: Record<string, unknown>): CohortCell {
  return {
    skill: (wire.skill as string | null) ?? null,
    arm: (wire.arm as string | null) ?? null,
    n: wire.n as number,
    timeToCompetence: mapTimeToCompetence(
      (wire.time_to_competence as Record<string, unknown>) ?? {}
    ),
    autonomy: mapAutonomy((wire.autonomy as Record<string, unknown>) ?? {}),
    orgEffect: mapOrgEffect((wire.org_effect as Record<string, unknown>) ?? {}),
  }
}

function mapStudentOverview(wire: Record<string, unknown>) {
  return {
    userId: wire.user_id as string,
    name: wire.name as string | null,
    email: wire.email as string | null,
    labsTotal: wire.labs_total as number,
    labsCompleted: wire.labs_completed as number,
    labsInProgress: wire.labs_in_progress as number,
    avgScore: wire.avg_score as number | null,
    totalHints: wire.total_hints as number,
    totalSessions: wire.total_sessions as number,
    lastActiveAt: wire.last_active_at as string | null,
  }
}
