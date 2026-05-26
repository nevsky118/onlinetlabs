import { notFound } from "next/navigation"
import { loadSession, SessionView } from "@/modules/session/server"

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
  } catch {
    notFound()
  }
}
