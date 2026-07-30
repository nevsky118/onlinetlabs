"use client"

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
import { formatRelativeTime } from "@/lib/format-duration"

function studentLabel(s: StudentOverview): string {
  return s.name ?? s.email ?? s.userId
}

export function InstructorView() {
  const t = useTranslations("dashboard.instructor.instructorView")
  const format = useFormatter()
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
        <p className="text-muted-foreground text-sm">{t("noStudents")}</p>
        <p className="text-muted-foreground max-w-xs text-xs">
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
        <StatCard
          label={t("activeToday")}
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
        placeholder={t("searchPlaceholder")}
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="max-w-sm rounded-none"
      />

      <div className="overflow-x-auto border">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
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
                      {t("inProgressBadge", { count: s.labsInProgress })}
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
                  {s.lastActiveAt
                    ? formatRelativeTime(s.lastActiveAt, format)
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 ? (
        <p className="text-muted-foreground py-8 text-center text-sm">
          {t("notFound")}
        </p>
      ) : null}
    </div>
  )
}
