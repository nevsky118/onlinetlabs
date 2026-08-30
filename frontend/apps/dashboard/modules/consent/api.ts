import type { ConsentDecision, ConsentRecord } from "./types"

const CONSENT_ENDPOINT = "/api/users/consent"
export const STUDY_SCOPE = "study"

export async function fetchConsentRecords(): Promise<ConsentRecord[]> {
  const response = await fetch(CONSENT_ENDPOINT, { cache: "no-store" })
  if (!response.ok) throw new Error(`fetchConsentRecords ${response.status}`)
  return response.json()
}

export async function recordStudyDecision(
  decision: ConsentDecision
): Promise<void> {
  const granted = decision === "granted"
  const response = await fetch(CONSENT_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scope: STUDY_SCOPE,
      observe: granted,
      act: granted,
      decision,
    }),
  })
  if (!response.ok) throw new Error(`recordStudyDecision ${response.status}`)
}

export async function revokeStudyConsent(): Promise<void> {
  const response = await fetch(`${CONSENT_ENDPOINT}?scope=${STUDY_SCOPE}`, {
    method: "DELETE",
  })
  if (!response.ok) throw new Error(`revokeStudyConsent ${response.status}`)
}
