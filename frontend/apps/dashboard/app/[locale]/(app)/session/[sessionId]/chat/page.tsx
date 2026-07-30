import { canViewAgentLogs } from "@repo/auth/server"
import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import { ChatView } from "@/modules/chat"
import { sessionStateQuery } from "@/modules/session"

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
  try {
    const [canViewLogs] = await Promise.all([
      canViewAgentLogs(),
      prefetchQuery(sessionStateQuery(sessionId)),
    ])
    return (
      <HydrateClient>
        <ChatView sessionId={sessionId} canViewLogs={canViewLogs} />
      </HydrateClient>
    )
  } catch {
    notFound()
  }
}
