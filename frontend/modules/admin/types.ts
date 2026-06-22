// Admin dashboard domain types (camelCase — mapped from snake_case backend)

export type UserRole = "student" | "instructor" | "admin"

export interface AdminUser {
  id: string
  name: string
  email: string
  image: string | null
  role: UserRole
  canSelectModel: boolean
  canViewAgentLogs: boolean
}

export interface AdminUsersPage {
  items: AdminUser[]
  total: number
  page: number
  pageSize: number
}

export type AdminUsersSort = "name" | "email" | "role"
export type AdminUsersOrder = "asc" | "desc"

export interface AdminUsersParams {
  page: number
  pageSize: number
  sort: AdminUsersSort
  order: AdminUsersOrder
  search: string
  role: UserRole | null
}

export interface AdminUserPatch {
  role?: UserRole
  canSelectModel?: boolean
  canViewAgentLogs?: boolean
}

export interface Overview {
  ab: {
    l2PassClosed: number
    l2PassOpen: number
    mentorHoursSaved: number
  }
  cohort: {
    pooledReachRate: number
    pooledN: number
  }
  identifier: {
    jOptimalTk: number
    recallAtOpt: number
    costs: Record<string, number>
  }
  ops: {
    activeSessions: number
    totalInterventions: number
    labeledRealN: number
  }
}

export interface IdentifierEval {
  curve: {
    tK: number
    latencyMedian: number | null
    falsePerHour: number
    recall: number
    j: number
  }[]
  jOptimalTk: number
  confusion: Record<string, Record<string, number>>
  firstMatch: {
    multiMatchRate: number
    orderSensitiveRate: number
    totalFiringSnapshots: number
  }
  costs: Record<string, number>
  preliminary: boolean
}

export interface TkSensitivity {
  points: {
    ratio: number
    tK: number
    j: number
  }[]
  costs: Record<string, number>
}

export interface ArmAnalysis {
  l2PassRateOpen: number
  l2PassRateClosed: number
  escalationsMeanOpen: number
  escalationsMeanClosed: number
  repeatedErrorsComparison: Record<string, unknown>
  mentorHoursSaved: number
}

// Cohort types — correct, do not change
export interface CohortMetricsRow {
  arm: string | null
  skill: string | null
  n: number
  reachRate: number | null
  medianCalendarSeconds: number | null
  medianActiveSeconds: number | null
  meanL1Interventions: number | null
}

export interface AdminCohortMetrics {
  rows: CohortMetricsRow[]
  headlineArm: string | null
}
