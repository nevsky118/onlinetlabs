export function formatRelative(isoString: string | null): string {
  if (!isoString) return "—"
  const diff = Math.max(
    0,
    Math.floor((Date.now() - new Date(isoString).getTime()) / 1000)
  )
  if (diff < 60) return "только что"
  const mins = Math.floor(diff / 60)
  if (mins < 60) return `${mins} мин назад`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} ч назад`
  const days = Math.floor(hrs / 24)
  return `${days} дн назад`
}

export function formatScore(score: number | null): string {
  return score === null ? "—" : `${Math.round(score)}`
}

const STATUS_LABELS: Record<string, string> = {
  // статусы лаб
  completed: "Завершена",
  in_progress: "В процессе",
  not_started: "Не начата",
  // статусы сессий
  active: "Активна",
  ended: "Завершена",
  error: "Ошибка",
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status
}

export type StatusVariant = "default" | "secondary" | "outline" | "destructive"

export function statusVariant(status: string): StatusVariant {
  if (status === "completed") return "default"
  if (status === "in_progress" || status === "active") return "secondary"
  if (status === "error") return "destructive"
  return "outline" // not_started, ended
}
