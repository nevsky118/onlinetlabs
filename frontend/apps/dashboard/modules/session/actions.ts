"use server"

import type {
  ActivityEvent,
  Credentials,
  FullSessionState,
  LaunchResult,
  Session,
} from "./types"
import {
  bulkNodeActionApi,
  controlSessionApi,
  getActivityApi,
  getCredentialsApi,
  getQueueStatusApi,
  getSessionApi,
  getSessionListApi,
  getSessionStateApi,
  launchSessionApi,
  nodeActionApi,
} from "./api"
import { SessionFetchError } from "./lib/errors"
import {
  mapCredentials,
  mapLaunch,
  mapQueued,
  mapSession,
  mapSessionList,
} from "./lib/mappings"

const QUEUED_STATUS = 202

export async function launchLab(labSlug: string): Promise<LaunchResult> {
  const res = await launchSessionApi(labSlug)

  if (res.status === QUEUED_STATUS) {
    return { kind: "queued", queued: mapQueued(await res.json()) }
  }
  if (res.ok) {
    return mapLaunch(await res.json())
  }

  // A denial carries a machine-readable code the caller branches on; anything
  // else is a genuine failure.
  const body = await res.json().catch(() => null)
  if (body?.code) {
    return { kind: "denied", code: body.code, detail: body.detail ?? "" }
  }
  throw new Error(`Launch failed: ${res.status}`)
}

export async function fetchQueueStatus(labSlug: string): Promise<{
  in_queue: boolean
  queue_position?: number
  queue_depth: number
  eta_sec?: number
}> {
  const res = await getQueueStatusApi(labSlug)
  if (!res.ok) throw new Error(`fetchQueueStatus ${res.status}`)
  return res.json()
}

export async function fetchCredentials(
  sessionId: string
): Promise<Credentials> {
  const res = await getCredentialsApi(sessionId)
  if (!res.ok)
    throw new SessionFetchError(res.status, "Credentials fetch failed")
  return mapCredentials(await res.json())
}

export async function fetchSession(sessionId: string): Promise<Session> {
  const res = await getSessionApi(sessionId)
  if (!res.ok) throw new Error("Session fetch failed")
  return mapSession(await res.json())
}

export async function stopLab(sessionId: string): Promise<void> {
  const res = await controlSessionApi(sessionId, "stop")
  if (!res.ok) throw new Error("Stop failed")
}

export async function restartLab(sessionId: string): Promise<void> {
  const res = await controlSessionApi(sessionId, "restart")
  if (!res.ok) throw new Error("Restart failed")
}

export async function resetLab(sessionId: string): Promise<void> {
  const res = await controlSessionApi(sessionId, "reset")
  if (!res.ok) throw new Error("Reset failed")
}

export async function endLab(sessionId: string): Promise<void> {
  const res = await controlSessionApi(sessionId, "end")
  if (!res.ok) throw new Error("End failed")
}

export async function fetchSessionState(
  sessionId: string
): Promise<FullSessionState> {
  const res = await getSessionStateApi(sessionId)
  if (!res.ok)
    throw new SessionFetchError(res.status, `fetchSessionState ${res.status}`)
  return res.json()
}

export async function nodeAction(
  sessionId: string,
  nodeId: string,
  action: string
): Promise<void> {
  const res = await nodeActionApi(sessionId, nodeId, action)
  if (!res.ok) throw new Error(`nodeAction ${res.status}`)
}

export async function bulkNodeAction(
  sessionId: string,
  action: string
): Promise<void> {
  const res = await bulkNodeActionApi(sessionId, action)
  if (!res.ok) throw new Error(`bulkNodeAction ${res.status}`)
}

export async function fetchSessionsList(): Promise<Session[]> {
  const res = await getSessionListApi()
  if (!res.ok) throw new SessionFetchError(res.status, "Sessions fetch failed")
  return mapSessionList(await res.json())
}

export async function fetchActivity(
  sessionId: string,
  params: { limit?: number; cursor?: string } = {}
): Promise<{ events: ActivityEvent[]; nextCursor: string | null }> {
  const res = await getActivityApi(sessionId, params)
  if (!res.ok) throw new Error(`fetchActivity ${res.status}`)
  return res.json()
}
