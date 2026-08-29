import { rethrowControlFlow } from "@repo/api/rethrow-control-flow"
import { canViewAgentLogs } from "@repo/auth/server"
import { notFound } from "next/navigation"
import { setRequestLocale } from "next-intl/server"
import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import {
  loadCredentials,
  SessionView,
  sessionStateQuery,
} from "@/modules/session/server"

export default async function SessionPage(props: {
  params: Promise<{ locale: string; sessionId: string }>
  searchParams: Promise<{ chat?: string }>
}) {
  const [{ locale, sessionId }, { chat }] = await Promise.all([
    props.params,
    props.searchParams,
  ])
  setRequestLocale(locale)
  try {
    const [credentials, canViewLogs] = await Promise.all([
      loadCredentials(sessionId),
      canViewAgentLogs(),
      prefetchQuery(sessionStateQuery(sessionId)),
    ])
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
  } catch (error) {
    rethrowControlFlow(error)
    notFound()
  }
}
