import "server-only"

import { authedFetch } from "@/lib/authed-fetch"

export async function getStudentsOverviewApi(): Promise<Response> {
  return authedFetch("/instructor/students")
}

export async function getStudentDetailApi(userId: string): Promise<Response> {
  return authedFetch(`/instructor/students/${encodeURIComponent(userId)}`)
}

export async function getSessionTimelineApi(
  userId: string,
  sessionId: string
): Promise<Response> {
  return authedFetch(
    `/instructor/students/${encodeURIComponent(userId)}/sessions/${encodeURIComponent(sessionId)}/timeline`
  )
}

export async function getCohortMetricsApi(byArm = false): Promise<Response> {
  return authedFetch(`/instructor/cohort-metrics?by_arm=${byArm}`)
}
