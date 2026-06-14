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
    // Нет backend-токена: нет сессии или она осиротела. Ведём на вход вместо
    // непрозрачной 500 в RSC/Server Action.
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

export async function getStudentsOverviewApi(): Promise<Response> {
  return authedFetch("/instructor/students")
}

export async function getStudentDetailApi(userId: string): Promise<Response> {
  return authedFetch(`/instructor/students/${encodeURIComponent(userId)}`)
}
