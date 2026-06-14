import "server-only"

import { getBackendToken } from "@/auth/token"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000"

async function authedFetch(
  path: string,
  init?: RequestInit
): Promise<Response> {
  const token = await getBackendToken()
  if (!token) {
    // Без токена прогресс не вернуть; отдаём 401-подобный ответ, вызывающий
    // трактует это как «нет данных» и не падает.
    return new Response(null, { status: 401 })
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

export async function getLabProgressApi(labSlug: string): Promise<Response> {
  return authedFetch(`/users/me/progress/labs/${encodeURIComponent(labSlug)}`)
}
