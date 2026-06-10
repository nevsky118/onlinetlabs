import "server-only"

import { headers } from "next/headers"
import { RedirectType, redirect } from "next/navigation"
import { getBackendToken } from "@/auth/token"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

async function authedFetch(
  path: string,
  init?: RequestInit
): Promise<Response> {
  const token = await getBackendToken()
  if (!token) {
    // Нет backend-токена: либо нет сессии, либо она осиротела (например, после
    // сброса БД остался валидный cookie без пользователя). Ведём на вход вместо
    // непрозрачной 500 в RSC/Server Action. replace, а не push: незалогиненным
    // на защищённую страницу всё равно не вернуться, в history её не держим.
    const referer = (await headers()).get("referer")
    const returnTo = referer
      ? new URL(referer).pathname + new URL(referer).search
      : "/"
    redirect(
      `/sign-in?redirect=${encodeURIComponent(returnTo)}`,
      RedirectType.replace
    )
  }
  return fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.headers || {}),
    },
    cache: "no-store",
  })
}

export async function launchSessionApi(labSlug: string): Promise<Response> {
  return authedFetch("/users/me/sessions", {
    method: "POST",
    body: JSON.stringify({ lab_slug: labSlug }),
  })
}

export async function getCredentialsApi(sessionId: string): Promise<Response> {
  return authedFetch(`/users/me/sessions/${sessionId}/credentials`)
}

export async function getSessionApi(sessionId: string): Promise<Response> {
  return authedFetch(`/users/me/sessions/${sessionId}`)
}

export async function getSessionListApi(): Promise<Response> {
  return authedFetch("/users/me/sessions")
}

export async function controlSessionApi(
  sessionId: string,
  action: "stop" | "restart" | "reset" | "end"
): Promise<Response> {
  return authedFetch(`/users/me/sessions/${sessionId}/${action}`, {
    method: "POST",
    body: "{}",
  })
}

export async function getSessionStateApi(sessionId: string): Promise<Response> {
  return authedFetch(`/users/me/sessions/${sessionId}/state`)
}

export async function nodeActionApi(
  sessionId: string,
  nodeId: string,
  action: string
): Promise<Response> {
  return authedFetch(
    `/users/me/sessions/${sessionId}/nodes/${nodeId}/${action}`,
    { method: "POST", body: "{}" }
  )
}

export async function bulkNodeActionApi(
  sessionId: string,
  action: string
): Promise<Response> {
  return authedFetch(`/users/me/sessions/${sessionId}/nodes/${action}`, {
    method: "POST",
    body: "{}",
  })
}

export async function getQueueStatusApi(labSlug: string): Promise<Response> {
  return authedFetch(
    `/users/me/sessions/queue-status?lab_slug=${encodeURIComponent(labSlug)}`
  )
}

export async function getActivityApi(
  sessionId: string,
  params: { limit?: number; cursor?: string }
): Promise<Response> {
  const qs = new URLSearchParams()
  if (params.limit !== undefined) qs.set("limit", String(params.limit))
  if (params.cursor) qs.set("cursor", params.cursor)
  return authedFetch(
    `/users/me/sessions/${sessionId}/activity?${qs.toString()}`
  )
}
