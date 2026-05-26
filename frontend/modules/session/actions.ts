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
  getSessionStateApi,
  launchSessionApi,
  nodeActionApi,
} from "./api"
import { mapCredentials, mapLaunch, mapSession } from "./lib/mappings"

export async function launchLab(labSlug: string): Promise<LaunchResult> {
  const res = await launchSessionApi(labSlug)
  if (res.status === 202) {
    const d = await res.json()
    return {
      kind: "queued",
      queued: {
        position: d.queue_position,
        depth: d.queue_depth,
        etaSec: d.eta_sec,
        labSlug: d.lab_slug,
      },
    }
  }
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`Launch failed: ${res.status} ${detail}`)
  }
  return mapLaunch(await res.json())
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
  if (!res.ok) throw new Error("Credentials fetch failed")
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
  if (!res.ok) throw new Error(`fetchSessionState ${res.status}`)
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

export async function fetchActivity(
  sessionId: string,
  params: { limit?: number; cursor?: string } = {}
): Promise<{ events: ActivityEvent[]; nextCursor: string | null }> {
  const res = await getActivityApi(sessionId, params)
  if (!res.ok) throw new Error(`fetchActivity ${res.status}`)
  return res.json()
}
