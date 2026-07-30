export function formatScore(score: number | null): string {
  return score === null ? "—" : `${Math.round(score)}`
}

// t = useTranslations("dashboard.instructor.statusLabels")
const STATUS_LABEL_KEYS: Record<string, string> = {
  completed: "completed",
  in_progress: "inProgress",
  not_started: "notStarted",
  active: "active",
  ended: "ended",
  error: "error",
}

export function statusLabel(
  status: string,
  t: (key: string) => string
): string {
  const key = STATUS_LABEL_KEYS[status]
  return key ? t(key) : status
}

export type StatusVariant = "default" | "secondary" | "outline" | "destructive"

export function statusVariant(status: string): StatusVariant {
  if (status === "completed") return "default"
  if (status === "in_progress" || status === "active") return "secondary"
  if (status === "error") return "destructive"
  return "outline" // not_started, ended
}
