import type { useFormatter } from "next-intl"

type Formatter = ReturnType<typeof useFormatter>
/**
 * Translator from useTranslations or getTranslations, scoped to the consumer module namespace.
 * Count-bearing keys must be ICU plurals.
 */
export type DurationT = (key: string, values?: Record<string, number>) => string

/**
 * Formats a past instant against now, "5 minutes ago" or "just now".
 * Intl.RelativeTimeFormat picks the unit and plural form from the locale.
 */
export function formatRelativeTime(iso: string, format: Formatter): string {
  return format.relativeTime(new Date(iso), new Date())
}

/**
 * Formats seconds with the largest units only, "2 hours 5 minutes" or "30 seconds".
 * Seconds are dropped past the first minute, so it suits ticking uptime.
 * @param t translator holding the seconds, minutes and hours keys
 */
export function formatDurationCoarse(
  totalSeconds: number,
  t: DurationT
): string {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  if (seconds < 60) return t("seconds", { count: seconds })
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return t("minutes", { count: minutes })
  const hours = Math.floor(minutes / 60)
  const remMinutes = minutes % 60
  return remMinutes > 0
    ? `${t("hours", { count: hours })} ${t("minutes", { count: remMinutes })}`
    : t("hours", { count: hours })
}

/**
 * Formats seconds down to second precision, "5 minutes 3 seconds" or "45 seconds".
 * Keeps seconds at any scale, so it suits live counters.
 * @param t translator holding the seconds, minutes and hours keys
 */
export function formatDurationFine(totalSeconds: number, t: DurationT): string {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const minutes = Math.floor(seconds / 60)
  const remSeconds = seconds % 60
  if (minutes < 60) {
    return remSeconds > 0
      ? `${t("minutes", { count: minutes })} ${t("seconds", { count: remSeconds })}`
      : t("minutes", { count: minutes })
  }
  const hours = Math.floor(minutes / 60)
  const remMinutes = minutes % 60
  return `${t("hours", { count: hours })} ${t("minutes", { count: remMinutes })}`
}

/**
 * Formats an approximate ETA, "less than a minute", "~5 minutes" or "~30 seconds".
 * @param t translator holding the lessThanMinute, aboutMinutes and aboutSeconds keys
 */
export function formatEtaApprox(etaSeconds: number, t: DurationT): string {
  if (etaSeconds <= 0) return t("lessThanMinute")
  if (etaSeconds > 60)
    return t("aboutMinutes", { count: Math.ceil(etaSeconds / 60) })
  return t("aboutSeconds", { count: Math.ceil(etaSeconds) })
}

/**
 * Formats an exact run duration given in milliseconds, "342 ms" or "1 minute 5 seconds".
 * @param t translator holding the milliseconds, seconds and minutes keys
 */
export function formatPreciseDuration(ms: number, t: DurationT): string {
  if (ms < 1000) return t("milliseconds", { count: Math.round(ms) })
  const totalSeconds = ms / 1000
  if (totalSeconds < 60) {
    return t("seconds", { count: Math.round(totalSeconds * 10) / 10 })
  }
  const minutes = Math.floor(totalSeconds / 60)
  const remSeconds = Math.round(totalSeconds % 60)
  return remSeconds > 0
    ? `${t("minutes", { count: minutes })} ${t("seconds", { count: remSeconds })}`
    : t("minutes", { count: minutes })
}
