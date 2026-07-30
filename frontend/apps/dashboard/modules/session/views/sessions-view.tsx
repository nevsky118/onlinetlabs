"use client"

import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import { Separator } from "@repo/design-system/ui/separator"
import { Link } from "@repo/i18n/navigation"
import { useFormatter, useTranslations } from "next-intl"
import type { Session } from "../types"
import { SessionCard } from "../components/session-card"
import { useSessionsList } from "../hooks/use-sessions-list"
import { formatRelativeTime } from "@/lib/format-duration"

export function SessionsView() {
  const t = useTranslations("dashboard.session.sessionsView")
  const format = useFormatter()
  // tick re-renders once a second for live uptime
  const { sessions, tick, refresh } = useSessionsList()

  const active = sessions.filter(
    (s) => s.status === "active" || s.status === "provisioning"
  )
  const recent = sessions.filter(
    (s) => s.status === "ended" || s.status === "error"
  )

  const now = Date.now() + tick * 0

  function getUptime(session: Session): number {
    if (session.status !== "active" && session.status !== "provisioning")
      return 0
    return Math.max(
      0,
      Math.floor((now - new Date(session.startedAt).getTime()) / 1000)
    )
  }

  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        <p className="text-muted-foreground text-sm">{t("emptyTitle")}</p>
        <p className="text-muted-foreground text-xs max-w-xs">
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
        <span className="text-muted-foreground text-xs">
          {t("activeCount", { count: active.length, max: 2 })}
        </span>
      </div>

      {active.length > 0 && (
        <section aria-labelledby="active-heading">
          <h2 id="active-heading" className="sr-only">
            {t("activeHeading")}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {active.map((s) => (
              <SessionCard
                key={s.id}
                session={s}
                uptimeSeconds={getUptime(s)}
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
            className="text-muted-foreground mb-4 text-xs tracking-wide uppercase"
          >
            {t("recentHeading")}
          </h2>
          <ul className="flex flex-col gap-0 divide-y border">
            {recent.map((s) => (
              <li key={s.id} className="flex items-center gap-3 px-4 py-3">
                <span
                  className={cn(
                    "size-2 rounded-full shrink-0",
                    s.status === "error"
                      ? "bg-destructive"
                      : "bg-muted-foreground"
                  )}
                  aria-hidden
                />
                <span className="flex-1 truncate text-sm font-medium">
                  {s.labTitle ?? s.labSlug}
                </span>
                <span className="text-muted-foreground hidden text-xs sm:inline">
                  {formatRelativeTime(s.endedAt ?? s.startedAt, format)}
                </span>
                <Button
                  nativeButton={false}
                  variant="ghost"
                  size="sm"
                  className="rounded-none text-xs"
                  render={<Link href={`/labs/${s.labSlug}`} />}
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
