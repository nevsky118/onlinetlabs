"use client"

import { formatRelativeTime } from "@/lib/format-duration"
import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import { Separator } from "@repo/design-system/ui/separator"
import { Link } from "@repo/i18n/navigation"
import { useFormatter, useTranslations } from "next-intl"
import type { Session } from "../types"
import { SessionCard } from "../components/session-card"
import { useSessionsList } from "../hooks/use-sessions-list"

export function SessionsView() {
  const t = useTranslations("dashboard.session.sessionsView")
  const format = useFormatter()
  // nowMs advances once a second for live uptime
  const { sessions, nowMs, refresh } = useSessionsList()

  const active = sessions.filter(
    (session) =>
      session.status === "active" || session.status === "provisioning"
  )
  const recent = sessions.filter(
    (session) => session.status === "ended" || session.status === "error"
  )

  function getUptime(session: Session): number {
    if (session.status !== "active" && session.status !== "provisioning")
      return 0
    return Math.max(
      0,
      Math.floor((nowMs - new Date(session.startedAt).getTime()) / 1000)
    )
  }

  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        <p className="text-sm text-muted-foreground">{t("emptyTitle")}</p>
        <p className="max-w-xs text-xs text-muted-foreground">
          {t("emptyDescription")}
        </p>
        <Button
          nativeButton={false}
          variant="outline"
          className="rounded-none"
          render={<Link href="/labs" />}
        >
          {t("goToLabs")}
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-end">
        <span className="text-xs text-muted-foreground">
          {t("activeCount", { count: active.length, max: 2 })}
        </span>
      </div>

      {active.length > 0 && (
        <section aria-labelledby="active-heading">
          <h2 id="active-heading" className="sr-only">
            {t("activeHeading")}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {active.map((session) => (
              <SessionCard
                key={session.id}
                session={session}
                uptimeSeconds={getUptime(session)}
                onEnded={refresh}
              />
            ))}
          </div>
        </section>
      )}

      {recent.length > 0 && (
        <section aria-labelledby="recent-heading">
          {active.length > 0 && <Separator className="mb-6" />}
          <h2
            id="recent-heading"
            className="mb-4 text-xs tracking-wide text-muted-foreground uppercase"
          >
            {t("recentHeading")}
          </h2>
          <ul className="flex flex-col gap-0 divide-y border">
            {recent.map((session) => (
              <li
                key={session.id}
                className="flex items-center gap-3 px-4 py-3"
              >
                <span
                  className={cn(
                    "size-2 shrink-0 rounded-full",
                    session.status === "error"
                      ? "bg-destructive"
                      : "bg-muted-foreground"
                  )}
                  aria-hidden
                />
                <span className="flex-1 truncate text-sm font-medium">
                  {session.labTitle ?? session.labSlug}
                </span>
                <span className="hidden text-xs text-muted-foreground sm:inline">
                  {formatRelativeTime(
                    session.endedAt ?? session.startedAt,
                    format
                  )}
                </span>
                <Button
                  nativeButton={false}
                  variant="ghost"
                  size="sm"
                  className="rounded-none text-xs"
                  aria-label={t("launchAgainAria", {
                    title: session.labTitle ?? session.labSlug,
                  })}
                  render={<Link href={`/labs/${session.labSlug}`} />}
                >
                  {t("launchAgain")}
                </Button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
