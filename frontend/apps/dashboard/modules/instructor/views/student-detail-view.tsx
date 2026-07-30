"use client"

import { Badge } from "@repo/design-system/ui/badge"
import { Button } from "@repo/design-system/ui/button"
import { Link } from "@repo/i18n/navigation"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft } from "lucide-react"
import { useFormatter, useTranslations } from "next-intl"
import { SessionDialogueSheet } from "../components/session-dialogue-sheet"
import { StatCard } from "../components/stat-card"
import { formatScore, statusLabel, statusVariant } from "../lib/format"
import { studentDetailQuery } from "../query"
import { formatRelativeTime } from "@/lib/format-duration"

export function StudentDetailView({ userId }: { userId: string }) {
  const t = useTranslations("dashboard.instructor.studentDetailView")
  const statusT = useTranslations("dashboard.instructor.statusLabels")
  const format = useFormatter()
  const { data, isPending } = useQuery(studentDetailQuery(userId))

  if (isPending) {
    return (
      <p className="text-muted-foreground py-24 text-center text-sm">
        {t("loading")}
      </p>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        <p className="text-muted-foreground text-sm">{t("notFound")}</p>
        <Button
          nativeButton={false}
          variant="outline"
          className="rounded-none"
          render={<Link href="/instructor" />}
        >
          <ArrowLeft className="mr-1 size-4" />
          {t("backToList")}
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3">
        <Button
          nativeButton={false}
          variant="ghost"
          size="sm"
          className="w-fit rounded-none px-0"
          render={<Link href="/instructor" />}
        >
          <ArrowLeft className="mr-1 size-4" />
          {t("allStudents")}
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
          label={t("labsCompleted")}
          value={data.labsCompleted}
          hint={t("labsInProgressHint", { count: data.labsInProgress })}
        />
        <StatCard label={t("avgScore")} value={formatScore(data.avgScore)} />
        <StatCard
          label={t("hints")}
          value={data.totalHints}
          hint={t("allTimeHint")}
        />
        <StatCard label={t("sessions")} value={data.totalSessions} />
      </div>

      <section className="flex flex-col gap-3">
        <h3 className="text-muted-foreground text-xs tracking-wide uppercase">
          {t("labsProgress")}
        </h3>
        {data.labs.length === 0 ? (
          <p className="text-muted-foreground border py-8 text-center text-sm">
            {t("noLabsStarted")}
          </p>
        ) : (
          <div className="overflow-x-auto border">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
                  <th className="px-4 py-3 font-medium">{t("headers.lab")}</th>
                  <th className="px-4 py-3 font-medium">
                    {t("headers.status")}
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    {t("headers.score")}
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    {t("headers.hints")}
                  </th>
                  <th className="px-4 py-3 text-right font-medium">
                    {t("headers.attempts")}
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
                        {statusLabel(lab.status, statusT)}
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
                      {lab.lastActiveAt
                        ? formatRelativeTime(lab.lastActiveAt, format)
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">{t("sessionsHeading")}</h2>
        {data.sessions.length === 0 ? (
          <p className="text-muted-foreground text-sm">{t("noSessions")}</p>
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
                        {statusLabel(s.status, statusT)}
                      </Badge>
                      {format.dateTime(new Date(s.startedAt), {
                        dateStyle: "short",
                        timeStyle: "short",
                      })}
                    </span>
                  </span>
                  <span className="text-muted-foreground text-xs">
                    {t("messageCountLine", {
                      messages: s.messageCount,
                      hints: s.hintCount,
                    })}
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
