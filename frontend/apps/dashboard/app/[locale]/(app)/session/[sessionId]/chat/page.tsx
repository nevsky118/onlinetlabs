import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import { ChatView } from "@/modules/chat"
import { sessionStateQuery } from "@/modules/session"
import { rethrowControlFlow } from "@repo/api/rethrow-control-flow"
import { canViewAgentLogs } from "@repo/auth/server"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { notFound } from "next/navigation"
import type { Metadata } from "next"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.sessionChat",
  })
  return { title: t("metaTitle") }
}

export default async function SessionChatPage(props: {
  params: Promise<{ locale: string; sessionId: string }>
}) {
  const { locale, sessionId } = await props.params
  setRequestLocale(locale)
  // Only the load is guarded: a render that throws must reach the error
  // boundary rather than be swallowed into a 404.
  const loaded = await Promise.all([
    canViewAgentLogs(),
    prefetchQuery(sessionStateQuery(sessionId)),
  ]).catch((error: unknown) => {
    rethrowControlFlow(error)
    return null
  })
  if (!loaded) notFound()

  const [canViewLogs] = loaded
  return (
    <HydrateClient>
      <ChatView sessionId={sessionId} canViewLogs={canViewLogs} />
    </HydrateClient>
  )
}
