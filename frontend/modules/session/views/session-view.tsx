"use client"

import { useEffect, useState } from "react"
import type { Credentials } from "../types"
import { ActivityCard } from "../components/activity-card"
import { ConsentGate } from "../components/consent-gate"
import { CredentialsCard } from "../components/credentials-card"
import { EscalateButton } from "../components/escalate-button"
import { NodeDetailDrawer } from "../components/node-detail-drawer"
import { NodesCard } from "../components/nodes-card"
import { SessionActions } from "../components/session-actions"
import { SessionHero } from "../components/session-hero"
import { SessionPageHeader } from "../components/session-page-header"
import { StickyMobileActionBar } from "../components/sticky-mobile-action-bar"
import { StreamStatusBanner } from "../components/stream-status-banner"
import { useSessionState } from "../hooks/use-session-state"
import { setAnalyticsContext } from "@/lib/analytics"
import { ChatInset, ChatPanel, ChatProvider, ChatTrigger } from "@/modules/chat"
import { ValidationButton } from "@/modules/validation"

export function SessionView({
  sessionId,
  credentials,
  chatOpen = false,
  canViewLogs = false,
}: {
  sessionId: string
  credentials: Credentials
  chatOpen?: boolean
  canViewLogs?: boolean
}) {
  const { state, streamStatus, actions } = useSessionState(sessionId)
  const [openNodeId, setOpenNodeId] = useState<string | null>(null)

  // Помечаем все фоновые события (page_view, idle, tab) этой сессии её
  // session_id и lab_slug, чтобы путь студента собирался воедино
  useEffect(() => {
    if (!state) return
    setAnalyticsContext(sessionId, state.lab.slug)
    return () => setAnalyticsContext(null, null)
  }, [sessionId, state])

  if (!state) return null

  const isEnded = state.status === "ended"

  return (
    <ChatProvider
      sessionId={sessionId}
      labSlug={state.lab.slug}
      canViewLogs={canViewLogs}
      defaultOpen={chatOpen}
    >
      <ChatInset>
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-6 pb-24 md:pb-6">
          <ConsentGate />
          <div className="flex items-center justify-between gap-3">
            <SessionPageHeader
              lab={state.lab}
              status={state.status}
              noAssist={state.noAssist}
            />
            <div className="flex shrink-0 items-center gap-2">
              <ChatTrigger />
              <EscalateButton sessionId={sessionId} />
              <ValidationButton
                sessionId={sessionId}
                labSlug={state.lab.slug}
              />
              <SessionActions
                sessionId={sessionId}
                status={state.status}
                labSlug={state.lab.slug}
              />
            </div>
          </div>
          <StreamStatusBanner status={streamStatus} />
          <SessionHero
            state={state}
            credentials={credentials}
            disabled={isEnded}
            onStopAll={() => actions.bulkNodeAction("stop")}
            onRestartAll={() => actions.bulkNodeAction("reload")}
          />
          <div className="grid gap-4 md:grid-cols-3">
            <NodesCard
              nodes={state.nodes}
              disabled={isEnded}
              loading={
                streamStatus === "connecting" && state.nodes.length === 0
              }
              onAction={actions.nodeAction}
              onOpenDetails={setOpenNodeId}
            />
            <ActivityCard sessionId={sessionId} />
            <CredentialsCard sessionId={sessionId} credentials={credentials} />
          </div>
          <StickyMobileActionBar
            status={state.status}
            credentials={credentials}
            onStopAll={() => actions.bulkNodeAction("stop")}
          />
          <NodeDetailDrawer
            nodeId={openNodeId}
            nodes={state.nodes}
            onClose={() => setOpenNodeId(null)}
            onAction={actions.nodeAction}
          />
        </div>
      </ChatInset>
      <ChatPanel />
    </ChatProvider>
  )
}
