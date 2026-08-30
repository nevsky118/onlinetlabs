import { queryOptions } from "@tanstack/react-query"
import type { ConsentRecord } from "./types"
import { STUDY_SCOPE, fetchConsentRecords } from "./api"

export const consentKeys = {
  all: ["consent"] as const,
  records: () => [...consentKeys.all, "records"] as const,
}

export function consentRecordsQuery() {
  return queryOptions({
    queryKey: consentKeys.records(),
    queryFn: fetchConsentRecords,
    select: (records: ConsentRecord[]) =>
      records.some(
        (record) =>
          record.scope === STUDY_SCOPE && record.decision === "granted"
      ),
    staleTime: 60_000,
  })
}
