"use server"

import type { StudentDetail, StudentsOverview } from "./types"
import { getStudentDetailApi, getStudentsOverviewApi } from "./api"

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
