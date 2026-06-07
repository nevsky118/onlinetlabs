"use client"

import Link from "next/link"
import type { Session } from "../types"
import { SessionCard } from "../components/session-card"
import { useSessionsList } from "../hooks/use-sessions-list"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"
import { Separator } from "@/ui/separator"

function formatRelative(isoString: string): string {
  const diff = Math.max(
    0,
    Math.floor((Date.now() - new Date(isoString).getTime()) / 1000)
  )
  if (diff < 60) return "только что"
  const mins = Math.floor(diff / 60)
  if (mins < 60) return `${mins} мин назад`
  const hrs = Math.floor(mins / 60)
  return `${hrs} ч назад`
}

export function SessionsView() {
  // tick перерисовывает раз в секунду для живого аптайма
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
        <p className="text-muted-foreground text-sm">Нет запущенных лаб</p>
        <p className="text-muted-foreground text-xs max-w-xs">
          Запустите лабораторию из каталога, чтобы начать обучение.
        </p>
        <Button variant="outline" className="rounded-none" asChild>
          <Link href="/labs">К лабам</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-end">
        <span className="text-muted-foreground text-xs">
          {active.length} / 2 активных
        </span>
      </div>

      {active.length > 0 && (
        <section aria-labelledby="active-heading">
          <h2 id="active-heading" className="sr-only">
            Активные
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
            Недавние
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
                  {s.endedAt
                    ? formatRelative(s.endedAt)
                    : formatRelative(s.startedAt)}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-none text-xs"
                  asChild
                >
                  <Link href={`/labs/${s.labSlug}`}>Запустить снова</Link>
                </Button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
