import "server-only"

import { fetchCredentials, fetchSession, fetchSessionState } from "./actions"
import { SessionView } from "./views/session-view"

export async function loadSession(sessionId: string) {
  const [state, credentials] = await Promise.all([
    fetchSessionState(sessionId),
    fetchCredentials(sessionId),
  ])
  return { state, credentials }
}

export { SessionView }
export { fetchSession }
