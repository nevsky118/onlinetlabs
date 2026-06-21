"use client"

import { useQuery } from "@tanstack/react-query"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { SessionDialogueSheet } from "../components/session-dialogue-sheet"
import { StatCard } from "../components/stat-card"
import {
  formatRelative,
  formatScore,
  statusLabel,
  statusVariant,
} from "../lib/format"
import { studentDetailQuery } from "../query"
import { Badge } from "@/ui/badge"
import { Button } from "@/ui/button"

export function StudentDetailView({ userId }: { userId: string }) {
  const { data, isPending } = useQuery(studentDetailQuery(userId))

  if (isPending) {
    return (
      <p className="text-muted-foreground py-24 text-center text-sm">
        Загрузка…
      </p>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        <p className="text-muted-foreground text-sm">Ученик не найден</p>
        <Button variant="outline" className="rounded-none" asChild>
          <Link href="/instructor">
            <ArrowLeft className="mr-1 size-4" />К списку
          </Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3">
        <Button
          variant="ghost"
          size="sm"
          className="w-fit rounded-none px-0"
          asChild
        >
          <Link href="/instructor">
            <ArrowLeft className="mr-1 size-4" />
            Все ученики
          </Link>
        </Button>
        <div>
          <h2 className="text-2xl font-semibold">
            {data.name ?? data.email ?? data.userId}
          </h2>
          {data.email ? (
            <p className="text-muted-foreground text-sm">{data.email}</p>
          ) : null}
        </div>
      </div>

      <div className="grid gap-px sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Завершено лаб"
          value={data.labsCompleted}
          hint={`${data.labsInProgress} в процессе`}
        />
        <StatCard label="Средний балл" value={formatScore(data.avgScore)} />
        <StatCard
          label="Подсказок"
          value={data.totalHints}
          hint="За всё время"
        />
        <StatCard label="Сессий" value={data.totalSessions} />
      </div>

      <section className="flex flex-col gap-3">
        <h3 className="text-muted-foreground text-xs tracking-wide uppercase">
          Прогресс по лабам
        </h3>
        {data.labs.length === 0 ? (
          <p className="text-muted-foreground border py-8 text-center text-sm">
            Ученик ещё не приступал к лабам
          </p>
        ) : (
          <div className="overflow-x-auto border">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
                  <th className="px-4 py-3 font-medium">Лаба</th>
                  <th className="px-4 py-3 font-medium">Статус</th>
                  <th className="px-4 py-3 text-right font-medium">Балл</th>
                  <th className="px-4 py-3 text-right font-medium">
                    Подсказки
                  </th>
                  <th className="px-4 py-3 text-right font-medium">Попытки</th>
                  <th className="px-4 py-3 text-right font-medium">Сессии</th>
                  <th className="px-4 py-3 text-right font-medium">
                    Активность
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.labs.map((lab) => (
                  <tr
                    key={lab.labSlug}
                    className="hover:bg-muted/50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/labs/${lab.labSlug}`}
                        className="font-medium hover:underline"
                      >
                        {lab.labTitle}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusVariant(lab.status)}>
                        {statusLabel(lab.status)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {formatScore(lab.score)}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {lab.hints}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {lab.attempts}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {lab.sessions}
                    </td>
                    <td className="text-muted-foreground px-4 py-3 text-right text-xs">
                      {formatRelative(lab.lastActiveAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Сессии</h2>
        {data.sessions.length === 0 ? (
          <p className="text-muted-foreground text-sm">Сессий пока нет.</p>
        ) : (
          <div className="flex flex-col gap-px border">
            {data.sessions.map((s) => (
              <SessionDialogueSheet
                key={s.sessionId}
                userId={userId}
                session={s}
              >
                <button
                  type="button"
                  className="hover:bg-muted flex w-full items-center justify-between bg-background px-4 py-3 text-left"
                >
                  <span className="flex flex-col gap-1">
                    <span className="text-sm font-medium">{s.labTitle}</span>
                    <span className="flex items-center gap-2 text-muted-foreground text-xs">
                      <Badge variant={statusVariant(s.status)}>
                        {statusLabel(s.status)}
                      </Badge>
                      {new Date(s.startedAt).toLocaleString()}
                    </span>
                  </span>
                  <span className="text-muted-foreground text-xs">
                    {s.messageCount} сообщ · {s.hintCount} подсказок
                  </span>
                </button>
              </SessionDialogueSheet>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
