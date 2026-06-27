"use server"

import type {
  AdminCohortMetrics,
  AdminDataPage,
  AdminDataParams,
  AdminLab,
  AdminLabPatch,
  AdminUser,
  AdminUserPatch,
  AdminUsersPage,
  AdminUsersParams,
  ArmAnalysis,
  CohortMetricsRow,
  IdentifierEval,
  Overview,
  TkSensitivity,
  UserRole,
} from "./types"
import {
  getAdminDataApi,
  getAdminLabsApi,
  getAdminUsersApi,
  getArmAnalysisApi,
  getCohortMetricsApi,
  getIdentifierEvalApi,
  getOverviewApi,
  getTkSensitivityApi,
  rebuildLabTemplateApi,
  updateAdminLabApi,
  updateAdminUserApi,
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

function mapAdminUser(d: Record<string, unknown>): AdminUser {
  return {
    id: d.id as string,
    name: d.name as string,
    email: d.email as string,
    image: (d.image as string) ?? null,
    role: d.role as UserRole,
    isActive: Boolean(d.is_active),
    canSelectModel: Boolean(d.can_select_model),
    canViewAgentLogs: Boolean(d.can_view_agent_logs),
  }
}

export async function fetchAdminUsers(
  params: AdminUsersParams
): Promise<AdminUsersPage> {
  const res = await getAdminUsersApi(params)
  if (!res.ok) throw new Error(`fetchAdminUsers ${res.status}`)
  const d = await res.json()
  return {
    items: (d.items as Record<string, unknown>[]).map(mapAdminUser),
    total: d.total as number,
    page: d.page as number,
    pageSize: d.page_size as number,
  }
}

export async function fetchAdminData(
  table: string,
  params: AdminDataParams
): Promise<AdminDataPage> {
  const res = await getAdminDataApi(table, params)
  if (!res.ok) throw new Error(`fetchAdminData ${res.status}`)
  const d = await res.json()
  return {
    items: d.items as AdminDataPage["items"],
    total: d.total as number,
    page: d.page as number,
    pageSize: d.page_size as number,
    columns: d.columns as string[],
    sortable: d.sortable as string[],
  }
}

export async function updateAdminUser(
  id: string,
  patch: AdminUserPatch
): Promise<{ ok: true; user: AdminUser } | { ok: false; error: string }> {
  const body: Record<string, unknown> = {}
  if (patch.role !== undefined) body.role = patch.role
  if (patch.isActive !== undefined) body.is_active = patch.isActive
  if (patch.canSelectModel !== undefined)
    body.can_select_model = patch.canSelectModel
  if (patch.canViewAgentLogs !== undefined)
    body.can_view_agent_logs = patch.canViewAgentLogs

  try {
    const res = await updateAdminUserApi(id, body)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return {
        ok: false,
        error: (err as { detail?: string }).detail ?? `Ошибка ${res.status}`,
      }
    }
    const d = await res.json()
    return { ok: true, user: mapAdminUser(d as Record<string, unknown>) }
  } catch {
    return { ok: false, error: "Сетевая ошибка" }
  }
}

function mapAdminLab(d: Record<string, unknown>): AdminLab {
  return {
    slug: d.slug as string,
    title: d.title as string,
    enabled: Boolean(d.enabled),
    environmentType: d.environment_type as string,
    courseSlug: (d.course_slug as string) ?? null,
    gns3TemplateProjectId: (d.gns3_template_project_id as string) ?? null,
    gns3TemplateProjectIdFrr:
      (d.gns3_template_project_id_frr as string) ?? null,
    gns3TemplateProjectIdIosvl2:
      (d.gns3_template_project_id_iosvl2 as string) ?? null,
    templateReady: Boolean(d.template_ready),
    templateStatus: (d.template_status as string) ?? "unknown",
  }
}

export async function fetchAdminLabs(): Promise<AdminLab[]> {
  const res = await getAdminLabsApi()
  if (!res.ok) throw new Error(`fetchAdminLabs ${res.status}`)
  const d = await res.json()
  return (d as Record<string, unknown>[]).map(mapAdminLab)
}

export async function updateAdminLab(
  slug: string,
  patch: AdminLabPatch
): Promise<{ ok: true; lab: AdminLab } | { ok: false; error: string }> {
  const body: Record<string, unknown> = {}
  if (patch.enabled !== undefined) body.enabled = patch.enabled
  if (patch.gns3TemplateProjectId !== undefined)
    body.gns3_template_project_id = patch.gns3TemplateProjectId
  if (patch.gns3TemplateProjectIdFrr !== undefined)
    body.gns3_template_project_id_frr = patch.gns3TemplateProjectIdFrr
  if (patch.gns3TemplateProjectIdIosvl2 !== undefined)
    body.gns3_template_project_id_iosvl2 = patch.gns3TemplateProjectIdIosvl2

  try {
    const res = await updateAdminLabApi(slug, body)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return {
        ok: false,
        error: (err as { detail?: string }).detail ?? `Ошибка ${res.status}`,
      }
    }
    const d = await res.json()
    return { ok: true, lab: mapAdminLab(d as Record<string, unknown>) }
  } catch {
    return { ok: false, error: "Сетевая ошибка" }
  }
}

export async function rebuildLabTemplate(
  slug: string
): Promise<{ ok: true } | { ok: false; error: string }> {
  try {
    const res = await rebuildLabTemplateApi(slug)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return {
        ok: false,
        error: (err as { detail?: string }).detail ?? `Ошибка ${res.status}`,
      }
    }
    return { ok: true }
  } catch {
    return { ok: false, error: "Сетевая ошибка" }
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
