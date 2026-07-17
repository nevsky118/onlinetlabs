export type SessionStatus = "provisioning" | "active" | "ended" | "error"

export type SessionData = {
  sessionId: string
  status: SessionStatus
  gns3Username: string
  gns3Password: string
  gns3Url: string
  gns3DeepUrl: string
}

export type QueuedResult = {
  position: number
  depth: number
  etaSec: number
  labSlug: string
}

export type LaunchResult =
  | { kind: "session"; session: SessionData }
  | { kind: "queued"; queued: QueuedResult }

export type Credentials = {
  gns3Username: string
  gns3Password: string
  gns3Url: string
  gns3DeepUrl: string
}

export type Session = {
  id: string
  labSlug: string
  labTitle: string | null
  status: SessionStatus
  startedAt: string
  endedAt: string | null
}

export type NodeStatus = "started" | "stopped" | "suspended"
export type StreamStatus = "connecting" | "live" | "degraded" | "polling"

export type Node = {
  id: string
  name: string
  nodeType: string
  status: NodeStatus
  console: number | null
  consoleType: string | null
  consoleHost: string
  symbol: string
}

export type LinkEndpoint = {
  nodeId: string
  adapterNumber: number
  portNumber: number
}

export type Link = {
  id: string
  nodes: LinkEndpoint[]
}

export type SessionMetrics = {
  nodesTotal: number
  nodesStarted: number
  linksCount: number
  uptimeSeconds: number
}

export type FullSessionState = {
  sessionId: string
  status: SessionStatus
  startedAt: string
  lab: { slug: string; title: string | null }
  nodes: Node[]
  links: Link[]
  metrics: SessionMetrics
  noAssist: boolean
}

export type ActivityEvent = {
  timestamp: string
  eventType: string
  componentId: string | null
  data: Record<string, unknown>
}

export type WSEvent =
  | { type: "snapshot"; timestamp: string; payload: FullSessionState }
  | {
      type: "node.status_changed"
      timestamp: string
      payload: { nodeId: string; status: NodeStatus }
    }
  | {
      type: "session.status_changed"
      timestamp: string
      payload: { status: SessionStatus }
    }
  | { type: "history.event"; timestamp: string; payload: ActivityEvent }
  | { type: "metrics.tick"; timestamp: string; payload: SessionMetrics }
  | {
      type: "state.invalidated"
      timestamp: string
      payload: Record<string, never>
    }
  | {
      type: "stream.degraded"
      timestamp: string
      payload: { reason: string }
    }
  | {
      type: "stream.restored"
      timestamp: string
      payload: Record<string, never>
    }
  | { type: "ping"; timestamp: string; payload: Record<string, never> }
