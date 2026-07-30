export interface StudentOverview {
  userId: string
  name: string | null
  email: string | null
  labsTotal: number
  labsCompleted: number
  labsInProgress: number
  avgScore: number | null
  totalHints: number
  totalSessions: number
  lastActiveAt: string | null
}

export interface StudentsOverview {
  students: StudentOverview[]
  totalStudents: number
  totalHints: number
}

export interface LabProgressRow {
  labSlug: string
  labTitle: string
  status: string
  score: number | null
  currentStep: number | null
  hints: number
  sessions: number
  attempts: number
  startedAt: string | null
  completedAt: string | null
  lastActiveAt: string | null
}

export interface SessionSummary {
  sessionId: string
  labSlug: string
  labTitle: string
  status: string
  startedAt: string
  endedAt: string | null
  messageCount: number
  hintCount: number
}

// Cohort metrics types
export interface TimeToCompetence {
  medianCalendarSeconds: number | null
  medianActiveSeconds: number | null
  reachRate: number | null
  reachRateAtHorizon: number | null
  restrictedMeanCalendarSeconds: number | null
  n: number
  censored: number
}

export interface Autonomy {
  meanL1Interventions: number | null
  meanL2Interventions: number | null
  meanSessionsToL2: number | null
}

export interface OrgEffect {
  l1EscalationsMean: number | null
  l2EscalationsMean: number | null
  l1RepeatedErrorsMean: number | null
  l2RepeatedErrorsMean: number | null
  note: string | null
}

export interface CohortCell {
  skill: string | null
  arm: string | null
  n: number
  timeToCompetence: TimeToCompetence
  autonomy: Autonomy
  orgEffect: OrgEffect
}

export interface CohortMetrics {
  bySkill: CohortCell[]
  pooled: CohortCell
  byArm: CohortCell[] | null
  headlineArm: string | null
}

export type TimelinePart = { type: string; text?: string }

export interface TimelineItem {
  kind: "student" | "tutor" | "intervention"
  ts: string
  parts: TimelinePart[] | null
  text: string | null
  action: string | null
  severity: string | null
  hintLevel: number | null
  struggleType: string | null
}

export interface StudentDetail {
  userId: string
  name: string | null
  email: string | null
  role: string
  labsCompleted: number
  labsInProgress: number
  avgScore: number | null
  totalHints: number
  totalSessions: number
  labs: LabProgressRow[]
  sessions: SessionSummary[]
}
