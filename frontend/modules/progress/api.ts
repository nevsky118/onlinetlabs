import "server-only"

import { getBackendToken } from "@/auth/token"
import { serverEnv } from "@/lib/env"

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

export async function getLabProgressApi(labSlug: string): Promise<Response> {
  return authedFetch(`/users/me/progress/labs/${encodeURIComponent(labSlug)}`)
}
