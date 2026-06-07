import "server-only"

import {
  type DefaultError,
  dehydrate,
  type FetchInfiniteQueryOptions,
  type FetchQueryOptions,
  HydrationBoundary,
  type QueryKey,
} from "@tanstack/react-query"
import type { ReactNode } from "react"
import { getQueryClient } from "./get-query-client"

export { getQueryClient }

export function HydrateClient({ children }: { children: ReactNode }) {
  const queryClient = getQueryClient()
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  )
}

export function prefetchQuery<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
>(options: FetchQueryOptions<TQueryFnData, TError, TData, TQueryKey>) {
  return getQueryClient().prefetchQuery(options)
}

export function prefetchInfiniteQuery<
  TQueryFnData,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = unknown,
>(
  options: FetchInfiniteQueryOptions<
    TQueryFnData,
    TError,
    TData,
    TQueryKey,
    TPageParam
  >
) {
  return getQueryClient().prefetchInfiniteQuery(options)
}
