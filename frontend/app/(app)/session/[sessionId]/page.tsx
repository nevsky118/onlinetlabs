import { notFound } from "next/navigation"
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
    const [credentials] = await Promise.all([
      loadCredentials(sessionId),
      prefetchQuery(sessionStateQuery(sessionId)),
    ])
    return (
      <HydrateClient>
        <SessionView
          sessionId={sessionId}
          credentials={credentials}
          chatOpen={chat === "1"}
        />
      </HydrateClient>
    )
  } catch {
    notFound()
  }
}
