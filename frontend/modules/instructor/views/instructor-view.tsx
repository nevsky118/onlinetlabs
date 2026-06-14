"use client"

import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { useMemo, useState } from "react"
import type { StudentOverview } from "../types"
import { StatCard } from "../components/stat-card"
import { formatRelative, formatScore } from "../lib/format"
import { studentsOverviewQuery } from "../query"
import { Badge } from "@/ui/badge"
import { Input } from "@/ui/input"

function studentLabel(s: StudentOverview): string {
  return s.name ?? s.email ?? s.userId
}

export function InstructorView() {
  const { data } = useQuery(studentsOverviewQuery())
  const [filter, setFilter] = useState("")

  const students = data?.students ?? []

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase()
    if (!q) return students
    return students.filter(
      (s) =>
        (s.name ?? "").toLowerCase().includes(q) ||
        (s.email ?? "").toLowerCase().includes(q)
    )
  }, [students, filter])

  if (students.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-24 text-center">
        <p className="text-muted-foreground text-sm">Пока нет учеников</p>
        <p className="text-muted-foreground max-w-xs text-xs">
          Как только ученики начнут проходить лабы, их прогресс появится здесь.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-px sm:grid-cols-3">
        <StatCard label="Учеников" value={data?.totalStudents ?? 0} />
        <StatCard
          label="Всего подсказок"
          value={data?.totalHints ?? 0}
          hint="Выданных агентом-тьютором"
        />
        <StatCard
          label="Активны сегодня"
          value={
            students.filter(
              (s) =>
                s.lastActiveAt &&
                Date.now() - new Date(s.lastActiveAt).getTime() <
                  24 * 60 * 60 * 1000
            ).length
          }
        />
      </div>

      <Input
        placeholder="Поиск по имени или email…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="max-w-sm rounded-none"
      />

      <div className="overflow-x-auto border">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
              <th className="px-4 py-3 font-medium">Ученик</th>
              <th className="px-4 py-3 text-right font-medium">Лабы</th>
              <th className="px-4 py-3 text-right font-medium">Ср. балл</th>
              <th className="px-4 py-3 text-right font-medium">Подсказки</th>
              <th className="px-4 py-3 text-right font-medium">Сессии</th>
              <th className="px-4 py-3 text-right font-medium">Активность</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filtered.map((s) => (
              <tr
                key={s.userId}
                className="hover:bg-muted/50 transition-colors"
              >
                <td className="px-4 py-3">
                  <Link
                    href={`/instructor/students/${s.userId}`}
                    className="flex flex-col hover:underline"
                  >
                    <span className="font-medium">{studentLabel(s)}</span>
                    {s.name && s.email ? (
                      <span className="text-muted-foreground text-xs">
                        {s.email}
                      </span>
                    ) : null}
                  </Link>
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  <span className="font-medium text-foreground">
                    {s.labsCompleted}
                  </span>
                  <span className="text-muted-foreground">
                    {" "}
                    / {s.labsTotal}
                  </span>
                  {s.labsInProgress > 0 ? (
                    <Badge variant="secondary" className="ml-2">
                      {s.labsInProgress} в работе
                    </Badge>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {formatScore(s.avgScore)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {s.totalHints}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {s.totalSessions}
                </td>
                <td className="text-muted-foreground px-4 py-3 text-right text-xs">
                  {formatRelative(s.lastActiveAt)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 ? (
        <p className="text-muted-foreground py-8 text-center text-sm">
          Ничего не найдено
        </p>
      ) : null}
    </div>
  )
}
