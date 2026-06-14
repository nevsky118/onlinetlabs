import { queryOptions } from "@tanstack/react-query"
import { fetchLabProgress } from "./actions"

export const progressKeys = {
  all: ["progress"] as const,
  lab: (slug: string) => [...progressKeys.all, "lab", slug] as const,
}

export function labProgressQuery(labSlug: string) {
  return queryOptions({
    queryKey: progressKeys.lab(labSlug),
    queryFn: () => fetchLabProgress(labSlug),
  })
}
