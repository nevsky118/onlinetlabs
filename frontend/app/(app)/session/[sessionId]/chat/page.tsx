import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import { ChatView } from "@/modules/chat"
import { sessionStateQuery } from "@/modules/session"

export const metadata: Metadata = { title: "Чат с тьютором" }

export default async function SessionChatPage(props: {
  params: Promise<{ sessionId: string }>
}) {
  const { sessionId } = await props.params
  try {
    await prefetchQuery(sessionStateQuery(sessionId))
    return (
      <HydrateClient>
        <ChatView sessionId={sessionId} />
      </HydrateClient>
    )
  } catch {
    notFound()
  }
}
