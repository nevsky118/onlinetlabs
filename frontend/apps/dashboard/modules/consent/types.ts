export type ConsentDecision = "granted" | "declined"

export type ConsentRecord = {
  scope: string
  decision: ConsentDecision
}
