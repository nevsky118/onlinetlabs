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
}
