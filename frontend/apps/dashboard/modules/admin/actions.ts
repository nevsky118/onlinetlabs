"use server"

import { rethrowControlFlow } from "@repo/api/rethrow-control-flow"
import { getTranslations } from "next-intl/server"
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
  const payload = await res.json()
  return {
    ab: {
      l2PassClosed: payload.ab.l2_pass_closed as number,
      l2PassOpen: payload.ab.l2_pass_open as number,
      mentorHoursSaved: payload.ab.mentor_hours_saved as number,
    },
    cohort: {
      pooledReachRate: payload.cohort.pooled_reach_rate as number,
      pooledN: payload.cohort.pooled_n as number,
    },
    identifier: {
      jOptimalTk: payload.identifier.j_optimal_t_k as number,
      recallAtOpt: payload.identifier.recall_at_opt as number,
      costs: payload.identifier.costs as Record<string, number>,
    },
    ops: {
      activeSessions: payload.ops.active_sessions as number,
      totalInterventions: payload.ops.total_interventions as number,
      finishedSessionsN: payload.ops.finished_sessions_n as number,
    },
  }
}

export async function fetchIdentifierEval(): Promise<IdentifierEval> {
  const res = await getIdentifierEvalApi()
  if (!res.ok) throw new Error(`fetchIdentifierEval ${res.status}`)
  const payload = await res.json()
  return {
    curve: ((payload.curve ?? []) as Record<string, unknown>[]).map((row) => ({
      tK: row.t_k as number,
      latencyMedian: (row.latency_median as number) ?? null,
      falsePerHour: row.false_per_hour as number,
      recall: row.recall as number,
      j: row.j as number,
    })),
    jOptimalTk: payload.j_optimal_t_k as number,
    confusion: payload.confusion as Record<string, Record<string, number>>,
    firstMatch: {
      multiMatchRate: payload.first_match.multi_match_rate as number,
      orderSensitiveRate: payload.first_match.order_sensitive_rate as number,
      totalFiringSnapshots: payload.first_match
        .total_firing_snapshots as number,
    },
    costs: payload.costs as Record<string, number>,
    preliminary: Boolean(payload.preliminary),
  }
}

export async function fetchTkSensitivity(): Promise<TkSensitivity> {
  const res = await getTkSensitivityApi()
  if (!res.ok) throw new Error(`fetchTkSensitivity ${res.status}`)
  const payload = await res.json()
  return {
    points: ((payload.points ?? []) as Record<string, unknown>[]).map(
      (row) => ({
        ratio: row.ratio as number,
        tK: row.t_k as number,
        // backend sends uppercase J
        j: row.J as number,
      })
    ),
    costs: payload.costs as Record<string, number>,
  }
}

export async function fetchArmAnalysis(): Promise<ArmAnalysis> {
  const res = await getArmAnalysisApi()
  if (!res.ok) throw new Error(`fetchArmAnalysis ${res.status}`)
  const payload = await res.json()
  return {
    l2PassRateOpen: payload.l2_pass_rate_open as number,
    l2PassRateClosed: payload.l2_pass_rate_closed as number,
    escalationsMeanOpen: payload.escalations_mean_open as number,
    escalationsMeanClosed: payload.escalations_mean_closed as number,
    repeatedErrorsComparison: payload.repeated_errors_comparison as Record<
      string,
      unknown
    >,
    mentorHoursSaved: payload.mentor_hours_saved as number,
  }
}

function mapAdminUser(payload: Record<string, unknown>): AdminUser {
  return {
    id: payload.id as string,
    name: payload.name as string,
    email: payload.email as string,
    image: (payload.image as string) ?? null,
    role: payload.role as UserRole,
    isActive: Boolean(payload.is_active),
    canSelectModel: Boolean(payload.can_select_model),
    canViewAgentLogs: Boolean(payload.can_view_agent_logs),
  }
}

export async function fetchAdminUsers(
  params: AdminUsersParams
): Promise<AdminUsersPage> {
  const res = await getAdminUsersApi(params)
  if (!res.ok) throw new Error(`fetchAdminUsers ${res.status}`)
  const payload = await res.json()
  return {
    items: (payload.items as Record<string, unknown>[]).map(mapAdminUser),
    total: payload.total as number,
    page: payload.page as number,
    pageSize: payload.page_size as number,
  }
}

export async function fetchAdminData(
  table: string,
  params: AdminDataParams
): Promise<AdminDataPage> {
  const res = await getAdminDataApi(table, params)
  if (!res.ok) throw new Error(`fetchAdminData ${res.status}`)
  const payload = await res.json()
  return {
    items: payload.items as AdminDataPage["items"],
    total: payload.total as number,
    page: payload.page as number,
    pageSize: payload.page_size as number,
    columns: payload.columns as string[],
    sortable: payload.sortable as string[],
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

  const t = await getTranslations("dashboard.admin.actionsErrors")
  try {
    const res = await updateAdminUserApi(id, body)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return {
        ok: false,
        error:
          (err as { detail?: string }).detail ??
          t("statusError", { status: res.status }),
      }
    }
    const payload = await res.json()
    return { ok: true, user: mapAdminUser(payload as Record<string, unknown>) }
  } catch (error) {
    rethrowControlFlow(error)
    return { ok: false, error: t("networkError") }
  }
}

function mapAdminLab(payload: Record<string, unknown>): AdminLab {
  return {
    slug: payload.slug as string,
    title: payload.title as string,
    enabled: Boolean(payload.enabled),
    environmentType: payload.environment_type as string,
    courseSlug: (payload.course_slug as string) ?? null,
    gns3TemplateProjectId: (payload.gns3_template_project_id as string) ?? null,
    gns3TemplateProjectIdFrr:
      (payload.gns3_template_project_id_frr as string) ?? null,
    gns3TemplateProjectIdIosvl2:
      (payload.gns3_template_project_id_iosvl2 as string) ?? null,
    templateReady: Boolean(payload.template_ready),
    templateStatus: (payload.template_status as string) ?? "unknown",
  }
}

export async function fetchAdminLabs(): Promise<AdminLab[]> {
  const res = await getAdminLabsApi()
  if (!res.ok) throw new Error(`fetchAdminLabs ${res.status}`)
  const payload = await res.json()
  return (payload as Record<string, unknown>[]).map(mapAdminLab)
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

  const t = await getTranslations("dashboard.admin.actionsErrors")
  try {
    const res = await updateAdminLabApi(slug, body)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return {
        ok: false,
        error:
          (err as { detail?: string }).detail ??
          t("statusError", { status: res.status }),
      }
    }
    const payload = await res.json()
    return { ok: true, lab: mapAdminLab(payload as Record<string, unknown>) }
  } catch (error) {
    rethrowControlFlow(error)
    return { ok: false, error: t("networkError") }
  }
}

export async function rebuildLabTemplate(
  slug: string
): Promise<{ ok: true } | { ok: false; error: string }> {
  const t = await getTranslations("dashboard.admin.actionsErrors")
  try {
    const res = await rebuildLabTemplateApi(slug)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return {
        ok: false,
        error:
          (err as { detail?: string }).detail ??
          t("statusError", { status: res.status }),
      }
    }
    return { ok: true }
  } catch (error) {
    rethrowControlFlow(error)
    return { ok: false, error: t("networkError") }
  }
}

function mapCohortRow(wire: Record<string, unknown>): CohortMetricsRow {
  return {
    arm: (wire.arm as string) ?? null,
    skill: (wire.skill as string) ?? null,
    n: wire.n as number,
    reachRate: (wire.reach_rate as number) ?? null,
    medianCalendarSeconds: (wire.median_calendar_seconds as number) ?? null,
    medianActiveSeconds: (wire.median_active_seconds as number) ?? null,
    meanL1Interventions: (wire.mean_l1_interventions as number) ?? null,
  }
}

export async function fetchAdminCohortMetrics(
  byArm = false
): Promise<AdminCohortMetrics> {
  const res = await getCohortMetricsApi(byArm)
  if (!res.ok) throw new Error(`fetchAdminCohortMetrics ${res.status}`)
  const payload = await res.json()
  const allRows: CohortMetricsRow[] = []
  if (payload.by_skill)
    allRows.push(
      ...(payload.by_skill as Record<string, unknown>[]).map(mapCohortRow)
    )
  if (payload.by_arm)
    allRows.push(
      ...(payload.by_arm as Record<string, unknown>[]).map(mapCohortRow)
    )
  if (payload.pooled)
    allRows.push(mapCohortRow(payload.pooled as Record<string, unknown>))
  return {
    rows: allRows,
    headlineArm: (payload.headline_arm as string) ?? null,
  }
}
