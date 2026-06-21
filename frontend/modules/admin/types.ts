// Admin dashboard domain types (camelCase — mapped from snake_case backend)

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
