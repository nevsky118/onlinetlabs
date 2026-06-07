import { queryOptions } from "@tanstack/react-query"
import { fetchChatHistory } from "./api"

export const chatKeys = {
  all: ["chat"] as const,
  history: (sessionId: string) =>
    [...chatKeys.all, "history", sessionId] as const,
}

export function chatHistoryQuery(sessionId: string) {
  return queryOptions({
    queryKey: chatKeys.history(sessionId),
    queryFn: ({ signal }) => fetchChatHistory(sessionId, signal),
  })
}
