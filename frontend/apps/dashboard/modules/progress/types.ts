export interface LabProgress {
  labSlug: string
  status: string
  score: number | null
  currentStep: number | null
  startedAt: string | null
  completedAt: string | null
}
