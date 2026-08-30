import { queryOptions } from "@tanstack/react-query"
import {
  fetchActiveSessionCount,
  fetchChatModels,
  fetchDefaultModelId,
} from "./api"

export const settingsKeys = {
  all: ["settings"] as const,
  models: () => [...settingsKeys.all, "models"] as const,
  defaultModel: () => [...settingsKeys.all, "default-model"] as const,
  accountSessions: () => [...settingsKeys.all, "account-sessions"] as const,
}

export function chatModelsQuery() {
  return queryOptions({
    queryKey: settingsKeys.models(),
    queryFn: fetchChatModels,
    staleTime: 5 * 60_000,
  })
}

export function defaultModelQuery() {
  return queryOptions({
    queryKey: settingsKeys.defaultModel(),
    queryFn: fetchDefaultModelId,
  })
}

export function accountSessionsQuery() {
  return queryOptions({
    queryKey: settingsKeys.accountSessions(),
    queryFn: fetchActiveSessionCount,
  })
}
