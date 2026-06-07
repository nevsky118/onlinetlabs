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

// На сервере клиент кешируется на время одного запроса (React cache),
// чтобы prefetchQuery и HydrateClient работали с одним инстансом.
const getServerQueryClient = cache(makeQueryClient)

let browserQueryClient: QueryClient | undefined

export function getQueryClient() {
  if (isServer) {
    return getServerQueryClient()
  }
  if (!browserQueryClient) browserQueryClient = makeQueryClient()
  return browserQueryClient
}
