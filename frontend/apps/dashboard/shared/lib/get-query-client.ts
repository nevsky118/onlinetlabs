import {
  defaultShouldDehydrateQuery,
  isServer,
  QueryClient,
} from "@tanstack/react-query"
import { cache } from "react"

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30 * 1000,
      },
      dehydrate: {
        shouldDehydrateQuery: (query) =>
          defaultShouldDehydrateQuery(query) ||
          query.state.status === "pending",
      },
    },
  })
}

// On the server the client is cached for the duration of a single request (React cache),
// so that prefetchQuery and HydrateClient work with the same instance.
const getServerQueryClient = cache(makeQueryClient)

let browserQueryClient: QueryClient | undefined

export function getQueryClient() {
  if (isServer) {
    return getServerQueryClient()
  }
  if (!browserQueryClient) browserQueryClient = makeQueryClient()
  return browserQueryClient
}
