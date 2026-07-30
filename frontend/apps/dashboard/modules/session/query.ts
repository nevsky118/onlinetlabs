import { infiniteQueryOptions, queryOptions } from "@tanstack/react-query"
import {
  fetchActivity,
  fetchQueueStatus,
  fetchSessionState,
  fetchSessionsList,
} from "./actions"

export type QueueStatusShape = {
  inQueue: boolean
  position: number
  depth: number
  etaSec: number
}

export const sessionKeys = {
  all: ["session"] as const,
  state: (id: string) => [...sessionKeys.all, "state", id] as const,
  list: () => [...sessionKeys.all, "list"] as const,
  activity: (id: string) => [...sessionKeys.all, "activity", id] as const,
  queue: (labSlug: string) => [...sessionKeys.all, "queue", labSlug] as const,
}

export function sessionStateQuery(id: string) {
  return queryOptions({
    queryKey: sessionKeys.state(id),
    queryFn: () => fetchSessionState(id),
  })
}

export function sessionsListQuery() {
  return queryOptions({
    queryKey: sessionKeys.list(),
    queryFn: () => fetchSessionsList(),
  })
}

export function queueStatusQuery(labSlug: string) {
  return queryOptions({
    queryKey: sessionKeys.queue(labSlug),
    queryFn: () => fetchQueueStatus(labSlug),
    select: (d): QueueStatusShape => ({
      inQueue: d.in_queue,
      position: d.queue_position ?? 0,
      depth: d.queue_depth ?? 0,
      etaSec: d.eta_sec ?? 0,
    }),
    refetchInterval: (query) => (query.state.data?.in_queue ? 5000 : false),
  })
}

export function activityFeedQuery(sessionId: string) {
  return infiniteQueryOptions({
    queryKey: sessionKeys.activity(sessionId),
    queryFn: ({ pageParam }) =>
      fetchActivity(sessionId, { limit: 20, cursor: pageParam }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
  })
}
