import { getBackendUserRole } from "@repo/auth/server"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@repo/design-system/components/page-header"
import { Separator } from "@repo/design-system/ui/separator"
import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import { getTranslations, setRequestLocale } from "next-intl/server"
import type { CohortCell } from "@/modules/instructor/types"
import { fetchCohortMetrics } from "@/modules/instructor/actions"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({
    locale,
    namespace: "dashboard.app.instructorCohort",
  })
  return { title: t("title"), description: t("description") }
}

function fmtDays(seconds: number | null): string {
  if (seconds === null) return "—"
  return (seconds / 86400).toFixed(1)
}

function fmtPct(rate: number | null): string {
  if (rate === null) return "—"
  return `${(rate * 100).toFixed(1)}%`
}

function fmtNum(v: number | null): string {
  if (v === null) return "—"
  return v.toFixed(2)
}

function CohortRow({
  row,
  allSkillsLabel,
}: {
  row: CohortCell
  allSkillsLabel: string
}) {
  return (
    <tr className="hover:bg-muted/50 transition-colors">
      <td className="px-4 py-3 font-medium">{row.skill ?? allSkillsLabel}</td>
      <td className="px-4 py-3 text-right tabular-nums">{row.n}</td>
      <td className="px-4 py-3 text-right tabular-nums">
        {fmtPct(row.timeToCompetence.reachRate)}
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        {fmtDays(row.timeToCompetence.medianCalendarSeconds)}
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        {fmtDays(row.timeToCompetence.medianActiveSeconds)}
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        {fmtNum(row.autonomy.meanL1Interventions)}
      </td>
      <td className="px-4 py-3 text-right tabular-nums text-muted-foreground">
        {row.timeToCompetence.censored}
      </td>
    </tr>
  )
}

export default async function CohortPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("dashboard.app.instructorCohort")

  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "instructor" && role !== "admin") forbidden()

  const metrics = await fetchCohortMetrics(false)

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{t("title")}</PageHeaderHeading>
        <PageHeaderDescription>{t("description")}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <div className="flex flex-col gap-6">
            {metrics.headlineArm ? (
              <p className="text-sm text-muted-foreground">
                {t("headlineArm")}{" "}
                <span className="font-mono">{metrics.headlineArm}</span>
              </p>
            ) : null}

            <div className="overflow-x-auto border">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
                    <th className="px-4 py-3 font-medium">
                      {t("headers.skill")}
                    </th>
                    <th className="px-4 py-3 text-right font-medium">N</th>
                    <th className="px-4 py-3 text-right font-medium">
                      Reach L2
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      {t("headers.medianCalendar")}
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      {t("headers.medianActive")}
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      {t("headers.interventions")}
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      {t("headers.censored")}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {metrics.bySkill.map((row) => (
                    <CohortRow
                      key={`${row.skill}__${row.arm}`}
                      row={row}
                      allSkillsLabel={t("allSkills")}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            <Separator />

            <div className="overflow-x-auto border">
              <table className="w-full border-collapse text-sm">
                <tbody>
                  <CohortRow
                    row={metrics.pooled}
                    allSkillsLabel={t("allSkills")}
                  />
                </tbody>
              </table>
            </div>

            <p className="text-sm text-muted-foreground">{t("honestyNote")}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
