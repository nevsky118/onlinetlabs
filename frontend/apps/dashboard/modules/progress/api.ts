import "server-only"
import { authedFetchOrThrow } from "@/lib/authed-fetch"

export async function getLabProgressApi(labSlug: string): Promise<Response> {
  return authedFetchOrThrow(
    `/users/me/progress/labs/${encodeURIComponent(labSlug)}`
  )
}
