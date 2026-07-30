import "server-only"

import { fetchCredentials } from "./actions"
import { SessionFetchError } from "./lib/errors"
import { SessionView } from "./views/session-view"
import { SessionsView } from "./views/sessions-view"

export async function loadCredentials(sessionId: string) {
  return fetchCredentials(sessionId)
}

export { SessionView }
export { SessionsView }
export { SessionFetchError }
export { sessionStateQuery, sessionsListQuery } from "./query"
