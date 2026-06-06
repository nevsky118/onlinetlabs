import "server-only"

import {
  fetchCredentials,
  fetchSession,
  fetchSessionState,
  fetchSessionsList,
} from "./actions"
import { SessionFetchError } from "./lib/errors"
import { SessionView } from "./views/session-view"
import { SessionsView } from "./views/sessions-view"

export async function loadSession(sessionId: string) {
  const [state, credentials] = await Promise.all([
    fetchSessionState(sessionId),
    fetchCredentials(sessionId),
  ])
  return { state, credentials }
}

export async function loadSessions() {
  try {
    return await fetchSessionsList()
  } catch (e) {
    if (e instanceof SessionFetchError) return []
    throw e
  }
}

export { SessionView }
export { SessionsView }
export { fetchSession }
export { SessionFetchError }
