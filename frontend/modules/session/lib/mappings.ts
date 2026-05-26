import type {
  Credentials,
  LaunchResult,
  Session,
  SessionStatus,
} from "../types"

type LaunchWire = {
  session_id: string
  status: string
  gns3_username: string
  gns3_password: string
  gns3_url: string
  gns3_deep_url: string
}

type CredentialsWire = {
  gns3_username: string
  gns3_password: string
  gns3_url: string
  gns3_deep_url: string
}

export function mapLaunch(w: LaunchWire): LaunchResult {
  return {
    kind: "session",
    session: {
      sessionId: w.session_id,
      status: w.status as SessionStatus,
      gns3Username: w.gns3_username,
      gns3Password: w.gns3_password,
      gns3Url: w.gns3_url,
      gns3DeepUrl: w.gns3_deep_url,
    },
  }
}

export function mapCredentials(w: CredentialsWire): Credentials {
  return {
    gns3Username: w.gns3_username,
    gns3Password: w.gns3_password,
    gns3Url: w.gns3_url,
    gns3DeepUrl: w.gns3_deep_url,
  }
}

type SessionWire = {
  id: string
  lab_slug: string
  lab_title?: string | null
  status: string
}

export function mapSession(w: SessionWire): Session {
  return {
    id: w.id,
    labSlug: w.lab_slug,
    labTitle: w.lab_title ?? null,
    status: w.status as SessionStatus,
  }
}
