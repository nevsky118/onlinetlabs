import type {
  Credentials,
  LaunchResult,
  QueuedResult,
  Session,
  SessionStatus,
} from "../types"

type LaunchWire = {
  session_id: string
  status: string
  gns3_username: string
  gns3_url: string
  gns3_deep_url: string
}

type QueuedWire = {
  queue_position: number
  queue_depth: number
  eta_sec: number
  lab_slug: string
}

type CredentialsWire = {
  gns3_username: string
  gns3_url: string
  gns3_deep_url: string
}

type SessionWire = {
  id: string
  lab_slug: string
  lab_title?: string | null
  status: string
  started_at: string
  ended_at: string | null
}

export function mapLaunch(wire: LaunchWire): LaunchResult {
  return {
    kind: "session",
    session: {
      sessionId: wire.session_id,
      status: wire.status as SessionStatus,
      gns3Username: wire.gns3_username,
      gns3Url: wire.gns3_url,
      gns3DeepUrl: wire.gns3_deep_url,
    },
  }
}

export function mapQueued(wire: QueuedWire): QueuedResult {
  return {
    position: wire.queue_position,
    depth: wire.queue_depth,
    etaSec: wire.eta_sec,
    labSlug: wire.lab_slug,
  }
}

export function mapCredentials(wire: CredentialsWire): Credentials {
  return {
    gns3Username: wire.gns3_username,
    gns3Url: wire.gns3_url,
    gns3DeepUrl: wire.gns3_deep_url,
  }
}

export function mapSession(wire: SessionWire): Session {
  return {
    id: wire.id,
    labSlug: wire.lab_slug,
    labTitle: wire.lab_title ?? null,
    status: wire.status as SessionStatus,
    startedAt: wire.started_at,
    endedAt: wire.ended_at ?? null,
  }
}

export function mapSessionList(rows: SessionWire[]): Session[] {
  return rows.map(mapSession)
}
