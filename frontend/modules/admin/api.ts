import "server-only"

import { headers } from "next/headers"
import { RedirectType, redirect } from "next/navigation"
import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

async function authedFetch(
  path: string,
  init?: RequestInit
): Promise<Response> {
  const token = await getBackendToken()
  if (!token) {
    const referer = (await headers()).get("referer")
    const returnTo = referer
      ? new URL(referer).pathname + new URL(referer).search
      : "/"
    redirect(
      `/sign-in?redirect=${encodeURIComponent(returnTo)}`,
      RedirectType.replace
    )
  }
  return fetch(`${serverEnv.BACKEND_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.headers || {}),
    },
    cache: "no-store",
  })
}

export async function getOverviewApi(): Promise<Response> {
  return authedFetch("/admin/overview")
}

export async function getIdentifierEvalApi(): Promise<Response> {
  return authedFetch("/admin/identifier-eval")
}

export async function getTkSensitivityApi(): Promise<Response> {
  return authedFetch("/admin/tk-sensitivity")
}

export async function getArmAnalysisApi(): Promise<Response> {
  return authedFetch("/experiment/arm-analysis")
}

export async function getCohortMetricsApi(byArm = false): Promise<Response> {
  return authedFetch(`/instructor/cohort-metrics?by_arm=${byArm}`)
}

export async function getAdminUsersApi(params: {
  page: number
  pageSize: number
  sort: string
  order: string
  search: string
  role: string | null
}): Promise<Response> {
  const qs = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
    sort: params.sort,
    order: params.order,
    search: params.search,
  })
  if (params.role) qs.set("role", params.role)
  return authedFetch(`/admin/users?${qs.toString()}`)
}

export async function updateAdminUserApi(
  id: string,
  patch: {
    role?: string
    can_select_model?: boolean
    can_view_agent_logs?: boolean
  }
): Promise<Response> {
  return authedFetch(`/admin/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  })
}
