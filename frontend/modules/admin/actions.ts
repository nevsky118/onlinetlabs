"use server"

import type {
  AdminCohortMetrics,
  ArmAnalysis,
  CohortMetricsRow,
  IdentifierEval,
  Overview,
  TkSensitivity,
} from "./types"
import {
  getArmAnalysisApi,
  getCohortMetricsApi,
  getIdentifierEvalApi,
  getOverviewApi,
  getTkSensitivityApi,
} from "./api"

export async function fetchOverview(): Promise<Overview> {
  const res = await getOverviewApi()
  if (!res.ok) throw new Error(`fetchOverview ${res.status}`)
  const d = await res.json()
  return {
    ab: {
      l2PassClosed: d.ab.l2_pass_closed as number,
      l2PassOpen: d.ab.l2_pass_open as number,
      mentorHoursSaved: d.ab.mentor_hours_saved as number,
    },
    cohort: {
      pooledReachRate: d.cohort.pooled_reach_rate as number,
      pooledN: d.cohort.pooled_n as number,
    },
    identifier: {
      jOptimalTk: d.identifier.j_optimal_t_k as number,
      recallAtOpt: d.identifier.recall_at_opt as number,
      costs: d.identifier.costs as Record<string, number>,
    },
    ops: {
      activeSessions: d.ops.active_sessions as number,
      totalInterventions: d.ops.total_interventions as number,
      labeledRealN: d.ops.labeled_real_n as number,
    },
  }
}

export async function fetchIdentifierEval(): Promise<IdentifierEval> {
  const res = await getIdentifierEvalApi()
  if (!res.ok) throw new Error(`fetchIdentifierEval ${res.status}`)
  const d = await res.json()
  return {
    curve: ((d.curve ?? []) as Record<string, unknown>[]).map((r) => ({
      tK: r.t_k as number,
      latencyMedian: (r.latency_median as number) ?? null,
      falsePerHour: r.false_per_hour as number,
      recall: r.recall as number,
      j: r.j as number,
    })),
    jOptimalTk: d.j_optimal_t_k as number,
    confusion: d.confusion as Record<string, Record<string, number>>,
    firstMatch: {
      multiMatchRate: d.first_match.multi_match_rate as number,
      orderSensitiveRate: d.first_match.order_sensitive_rate as number,
      totalFiringSnapshots: d.first_match.total_firing_snapshots as number,
    },
    costs: d.costs as Record<string, number>,
    preliminary: Boolean(d.preliminary),
  }
}

export async function fetchTkSensitivity(): Promise<TkSensitivity> {
  const res = await getTkSensitivityApi()
  if (!res.ok) throw new Error(`fetchTkSensitivity ${res.status}`)
  const d = await res.json()
  return {
    points: ((d.points ?? []) as Record<string, unknown>[]).map((r) => ({
      ratio: r.ratio as number,
      tK: r.t_k as number,
      // backend sends uppercase J
      j: r.J as number,
    })),
    costs: d.costs as Record<string, number>,
  }
}

export async function fetchArmAnalysis(): Promise<ArmAnalysis> {
  const res = await getArmAnalysisApi()
  if (!res.ok) throw new Error(`fetchArmAnalysis ${res.status}`)
  const d = await res.json()
  return {
    l2PassRateOpen: d.l2_pass_rate_open as number,
    l2PassRateClosed: d.l2_pass_rate_closed as number,
    escalationsMeanOpen: d.escalations_mean_open as number,
    escalationsMeanClosed: d.escalations_mean_closed as number,
    repeatedErrorsComparison: d.repeated_errors_comparison as Record<
      string,
      unknown
    >,
    mentorHoursSaved: d.mentor_hours_saved as number,
  }
}

export async function fetchAdminCohortMetrics(
  byArm = false
): Promise<AdminCohortMetrics> {
  const res = await getCohortMetricsApi(byArm)
  if (!res.ok) throw new Error(`fetchAdminCohortMetrics ${res.status}`)
  const d = await res.json()
  const mapRow = (r: Record<string, unknown>): CohortMetricsRow => ({
    arm: (r.arm as string) ?? null,
    skill: (r.skill as string) ?? null,
    n: r.n as number,
    reachRate: (r.reach_rate as number) ?? null,
    medianCalendarSeconds: (r.median_calendar_seconds as number) ?? null,
    medianActiveSeconds: (r.median_active_seconds as number) ?? null,
    meanL1Interventions: (r.mean_l1_interventions as number) ?? null,
  })
  const allRows: CohortMetricsRow[] = []
  if (d.by_skill)
    allRows.push(...(d.by_skill as Record<string, unknown>[]).map(mapRow))
  if (d.by_arm)
    allRows.push(...(d.by_arm as Record<string, unknown>[]).map(mapRow))
  if (d.pooled) allRows.push(mapRow(d.pooled as Record<string, unknown>))
  return {
    rows: allRows,
    headlineArm: (d.headline_arm as string) ?? null,
  }
}
