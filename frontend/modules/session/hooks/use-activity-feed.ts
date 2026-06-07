"use client"

import { useInfiniteQuery } from "@tanstack/react-query"
import { activityFeedQuery } from "../query"

export function useActivityFeed(sessionId: string) {
  const query = useInfiniteQuery(activityFeedQuery(sessionId))
  const events = query.data?.pages.flatMap((p) => p.events) ?? []
  return {
    events,
    hasMore: query.hasNextPage,
    loading: query.isFetchingNextPage || query.isLoading,
    loadMore: () => {
      void query.fetchNextPage()
    },
  }
}
