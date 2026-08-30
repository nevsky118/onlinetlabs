import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import {
  loadCredentials,
  SessionView,
  sessionStateQuery,
} from "@/modules/session/server"
import { rethrowControlFlow } from "@repo/api/rethrow-control-flow"
import { canViewAgentLogs } from "@repo/auth/server"
import { setRequestLocale } from "next-intl/server"
import { notFound } from "next/navigation"

export default async function SessionPage(props: {
  params: Promise<{ locale: string; sessionId: string }>
  searchParams: Promise<{ chat?: string }>
}) {
  const [{ locale, sessionId }, { chat }] = await Promise.all([
    props.params,
    props.searchParams,
  ])
  setRequestLocale(locale)
  // Only the load is guarded: a render that throws must reach the error
  // boundary rather than be swallowed into a 404.
  const loaded = await Promise.all([
    loadCredentials(sessionId),
    canViewAgentLogs(),
    prefetchQuery(sessionStateQuery(sessionId)),
  ]).catch((error: unknown) => {
    rethrowControlFlow(error)
    return null
  })
  if (!loaded) notFound()

  const [credentials, canViewLogs] = loaded
  return (
    <HydrateClient>
      <SessionView
        sessionId={sessionId}
        credentials={credentials}
        chatOpen={chat === "1"}
        canViewLogs={canViewLogs}
      />
    </HydrateClient>
  )
}
