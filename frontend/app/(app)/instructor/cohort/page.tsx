import type { Metadata } from "next"
import { forbidden, unauthorized } from "next/navigation"
import type { CohortCell } from "@/modules/instructor/types"
import { getBackendUserRole } from "@/auth/role"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { fetchCohortMetrics } from "@/modules/instructor/actions"
import { Separator } from "@/ui/separator"

const title = "Когортные метрики"
const description = "Время до компетентности, автономия и орг-эффект по скиллам"

export const metadata: Metadata = { title, description }

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

function CohortRow({ row }: { row: CohortCell }) {
  return (
    <tr className="hover:bg-muted/50 transition-colors">
      <td className="px-4 py-3 font-medium">{row.skill ?? "Все навыки"}</td>
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

export default async function CohortPage() {
  const role = await getBackendUserRole()
  if (role === null) unauthorized()
  if (role !== "instructor" && role !== "admin") forbidden()

  const metrics = await fetchCohortMetrics(false)

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <div className="flex flex-col gap-6">
            {metrics.headlineArm ? (
              <p className="text-sm text-muted-foreground">
                Плечо: <span className="font-mono">{metrics.headlineArm}</span>
              </p>
            ) : null}

            <div className="overflow-x-auto border">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="text-muted-foreground border-b text-left text-xs tracking-wide uppercase">
                    <th className="px-4 py-3 font-medium">Скилл</th>
                    <th className="px-4 py-3 text-right font-medium">N</th>
                    <th className="px-4 py-3 text-right font-medium">
                      Reach L2
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      Медиана кал., дн
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      Медиана акт., дн
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      L1→L2 интерв.
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      Цензурир.
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {metrics.bySkill.map((row) => (
                    <CohortRow key={`${row.skill}__${row.arm}`} row={row} />
                  ))}
                </tbody>
              </table>
            </div>

            <Separator />

            <div className="overflow-x-auto border">
              <table className="w-full border-collapse text-sm">
                <tbody>
                  <CohortRow row={metrics.pooled} />
                </tbody>
              </table>
            </div>

            <p className="text-sm text-muted-foreground">
              D4-тренд описательный (survivorship); дельта плеч = Задача 4
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
