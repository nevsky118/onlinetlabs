import { queryOptions } from "@tanstack/react-query"
import {
  fetchSessionTimeline,
  fetchStudentDetail,
  fetchStudentsOverview,
} from "./actions"

export const instructorKeys = {
  all: ["instructor"] as const,
  students: () => [...instructorKeys.all, "students"] as const,
  student: (id: string) => [...instructorKeys.all, "student", id] as const,
}

export function studentsOverviewQuery() {
  return queryOptions({
    queryKey: instructorKeys.students(),
    queryFn: () => fetchStudentsOverview(),
  })
}

export function studentDetailQuery(userId: string) {
  return queryOptions({
    queryKey: instructorKeys.student(userId),
    queryFn: () => fetchStudentDetail(userId),
  })
}

export function sessionTimelineQuery(userId: string, sessionId: string) {
  return queryOptions({
    queryKey: [
      ...instructorKeys.student(userId),
      "timeline",
      sessionId,
    ] as const,
    queryFn: () => fetchSessionTimeline(userId, sessionId),
  })
}
