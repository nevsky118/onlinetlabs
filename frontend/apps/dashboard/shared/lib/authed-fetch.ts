import { createAuthedFetch } from "@repo/api/authed-fetch"
import { getBackendToken } from "@repo/auth/server"

export const authedFetch = createAuthedFetch(getBackendToken)
// progress returns 401 instead of redirecting
export const authedFetchOrThrow = createAuthedFetch(getBackendToken, {
  onMissingToken: "throw",
})
