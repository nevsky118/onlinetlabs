import { notFound } from "next/navigation"
import {
  loadSession,
  SessionFetchError,
  SessionView,
} from "@/modules/session/server"

export default async function SessionPage(props: {
  params: Promise<{ sessionId: string }>
}) {
  const { sessionId } = await props.params
  try {
    const { state, credentials } = await loadSession(sessionId)
    return (
      <SessionView
        sessionId={sessionId}
        initialState={state}
        credentials={credentials}
      />
    )
  } catch (err) {
    // 5xx пробрасываем в error boundary; клиентские причины (401/403/404) → not-found.
    if (err instanceof SessionFetchError) {
      if (err.status >= 500) throw err
      notFound()
    }
    throw err
  }
}
