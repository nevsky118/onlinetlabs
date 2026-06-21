import { notFound } from "next/navigation"
import { canViewAgentLogs } from "@/auth/role"
import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import {
  loadCredentials,
  SessionView,
  sessionStateQuery,
} from "@/modules/session/server"

export default async function SessionPage(props: {
  params: Promise<{ sessionId: string }>
  searchParams: Promise<{ chat?: string }>
}) {
  const [{ sessionId }, { chat }] = await Promise.all([
    props.params,
    props.searchParams,
  ])
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
  } catch {
    notFound()
  }
}
