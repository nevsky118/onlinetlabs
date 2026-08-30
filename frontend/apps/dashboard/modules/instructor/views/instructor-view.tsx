"use client"

import { formatRelativeTime } from "@/lib/format-duration"
import { Badge } from "@repo/design-system/ui/badge"
import { Input } from "@repo/design-system/ui/input"
import { Link } from "@repo/i18n/navigation"
import { useQuery } from "@tanstack/react-query"
import { useFormatter, useTranslations } from "next-intl"
import { useMemo, useState } from "react"
import type { StudentOverview } from "../types"
import { StatCard } from "../components/stat-card"
import { formatScore } from "../lib/format"
import { studentsOverviewQuery } from "../query"

function studentLabel(student: StudentOverview): string {
  return student.name ?? student.email ?? student.userId
}

const NO_STUDENTS: StudentOverview[] = []
const ACTIVE_WINDOW_MS = 24 * 60 * 60 * 1000

export function InstructorView() {
  const t = useTranslations("dashboard.instructor.instructorView")
  const format = useFormatter()
  const { data, dataUpdatedAt } = useQuery(studentsOverviewQuery())
  // Anchored to the fetch time, not to Date.now() during render.
  const activeSince = dataUpdatedAt - ACTIVE_WINDOW_MS
  const [filter, setFilter] = useState("")

  // A stable empty array, so the memo below is not invalidated on every render.
  const students = data?.students ?? NO_STUDENTS

  const filtered = useMemo(() => {
    const needle = filter.trim().toLowerCase()
    if (!needle) return students
    return students.filter(
      (student) =>
        (student.name ?? "").toLowerCase().includes(needle) ||
        (student.email ?? "").toLowerCase().includes(needle)
    )
  }, [students, filter])

  const activeToday = students.filter(
    (student) =>
      student.lastActiveAt !== null &&
      activeSince - new Date(student.lastActiveAt).getTime() < 0
  ).length

  if (students.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-24 text-center">
        <p className="text-sm text-muted-foreground">{t("noStudents")}</p>
        <p className="max-w-xs text-xs text-muted-foreground">
          {t("noStudentsHint")}
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-px sm:grid-cols-3">
        <StatCard label={t("students")} value={data?.totalStudents ?? 0} />
        <StatCard
          label={t("totalHints")}
          value={data?.totalHints ?? 0}
          hint={t("totalHintsHint")}
        />
        <StatCard label={t("activeToday")} value={activeToday} />
      </div>

      <Input
        placeholder={t("searchPlaceholder")}
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
        className="max-w-sm rounded-none"
      />

      <div className="overflow-x-auto border">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-xs tracking-wide text-muted-foreground uppercase">
              <th className="px-4 py-3 font-medium">{t("headers.student")}</th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.labs")}
              </th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.avgScore")}
              </th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.hints")}
              </th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.sessions")}
              </th>
              <th className="px-4 py-3 text-right font-medium">
                {t("headers.activity")}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filtered.map((student) => (
              <tr
                key={student.userId}
                className="transition-colors hover:bg-muted/50"
              >
                <td className="px-4 py-3">
                  <Link
                    href={`/instructor/students/${student.userId}`}
                    className="flex flex-col hover:underline"
                  >
                    <span className="font-medium">{studentLabel(student)}</span>
                    {student.name && student.email ? (
                      <span className="text-xs text-muted-foreground">
                        {student.email}
                      </span>
                    ) : null}
                  </Link>
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  <span className="font-medium text-foreground">
                    {student.labsCompleted}
                  </span>
                  <span className="text-muted-foreground">
                    {" "}
                    / {student.labsTotal}
                  </span>
                  {student.labsInProgress > 0 ? (
                    <Badge variant="secondary" className="ml-2">
                      {t("inProgressBadge", { count: student.labsInProgress })}
                    </Badge>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {formatScore(student.avgScore)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {student.totalHints}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {student.totalSessions}
                </td>
                <td className="px-4 py-3 text-right text-xs text-muted-foreground">
                  {student.lastActiveAt
                    ? formatRelativeTime(student.lastActiveAt, format)
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          {t("notFound")}
        </p>
      ) : null}
    </div>
  )
}
