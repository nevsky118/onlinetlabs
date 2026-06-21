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
  const d = await res.json()
  return {
    students: (d.students ?? []).map(mapStudentOverview),
    totalStudents: d.total_students,
    totalHints: d.total_hints,
  }
}

export async function fetchStudentDetail(
  userId: string
): Promise<StudentDetail | null> {
  const res = await getStudentDetailApi(userId)
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`fetchStudentDetail ${res.status}`)
  const d = await res.json()
  return {
    userId: d.user_id,
    name: d.name,
    email: d.email,
    role: d.role,
    labsCompleted: d.labs_completed,
    labsInProgress: d.labs_in_progress,
    avgScore: d.avg_score,
    totalHints: d.total_hints,
    totalSessions: d.total_sessions,
    labs: (d.labs ?? []).map((l: Record<string, unknown>) => ({
      labSlug: l.lab_slug,
      labTitle: l.lab_title,
      status: l.status,
      score: l.score,
      currentStep: l.current_step,
      hints: l.hints,
      sessions: l.sessions,
      attempts: l.attempts,
      startedAt: l.started_at,
      completedAt: l.completed_at,
      lastActiveAt: l.last_active_at,
    })),
    sessions: (d.sessions ?? []).map((s: Record<string, unknown>) => ({
      sessionId: s.session_id,
      labSlug: s.lab_slug,
      labTitle: s.lab_title,
      status: s.status,
      startedAt: s.started_at,
      endedAt: s.ended_at,
      messageCount: s.message_count,
      hintCount: s.hint_count,
    })),
  }
}

export async function fetchSessionTimeline(
  userId: string,
  sessionId: string
): Promise<TimelineItem[]> {
  const res = await getSessionTimelineApi(userId, sessionId)
  if (!res.ok) throw new Error(`fetchSessionTimeline ${res.status}`)
  const rows = (await res.json()) as Record<string, unknown>[]
  return rows.map((r) => ({
    kind: r.kind as TimelineItem["kind"],
    ts: r.ts as string,
    parts: (r.parts as TimelineItem["parts"]) ?? null,
    text: (r.text as string) ?? null,
    action: (r.action as string) ?? null,
    severity: (r.severity as string) ?? null,
    hintLevel: (r.hint_level as number) ?? null,
    struggleType: (r.struggle_type as string) ?? null,
  }))
}

export async function fetchCohortMetrics(
  byArm = false
): Promise<CohortMetrics> {
  const res = await getCohortMetricsApi(byArm)
  if (!res.ok) throw new Error(`fetchCohortMetrics ${res.status}`)
  const d = await res.json()
  return {
    bySkill: (d.by_skill ?? []).map(mapCohortCell),
    pooled: mapCohortCell(d.pooled),
    byArm: d.by_arm
      ? (d.by_arm as Record<string, unknown>[]).map(mapCohortCell)
      : null,
    headlineArm: (d.headline_arm as string) ?? null,
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

function mapAutonomy(a: Record<string, unknown>): Autonomy {
  return {
    meanL1Interventions: (a.mean_l1_interventions as number) ?? null,
    meanL2Interventions: (a.mean_l2_interventions as number) ?? null,
    meanSessionsToL2: (a.mean_sessions_to_l2 as number) ?? null,
  }
}

function mapOrgEffect(o: Record<string, unknown>): OrgEffect {
  return {
    l1EscalationsMean: (o.l1_escalations_mean as number) ?? null,
    l2EscalationsMean: (o.l2_escalations_mean as number) ?? null,
    l1RepeatedErrorsMean: (o.l1_repeated_errors_mean as number) ?? null,
    l2RepeatedErrorsMean: (o.l2_repeated_errors_mean as number) ?? null,
    note: (o.note as string) ?? null,
  }
}

function mapCohortCell(c: Record<string, unknown>): CohortCell {
  return {
    skill: (c.skill as string | null) ?? null,
    arm: (c.arm as string | null) ?? null,
    n: c.n as number,
    timeToCompetence: mapTimeToCompetence(
      (c.time_to_competence as Record<string, unknown>) ?? {}
    ),
    autonomy: mapAutonomy((c.autonomy as Record<string, unknown>) ?? {}),
    orgEffect: mapOrgEffect((c.org_effect as Record<string, unknown>) ?? {}),
  }
}

function mapStudentOverview(s: Record<string, unknown>) {
  return {
    userId: s.user_id as string,
    name: s.name as string | null,
    email: s.email as string | null,
    labsTotal: s.labs_total as number,
    labsCompleted: s.labs_completed as number,
    labsInProgress: s.labs_in_progress as number,
    avgScore: s.avg_score as number | null,
    totalHints: s.total_hints as number,
    totalSessions: s.total_sessions as number,
    lastActiveAt: s.last_active_at as string | null,
  }
}
