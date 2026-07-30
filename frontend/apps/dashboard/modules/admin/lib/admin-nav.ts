import {
  Fingerprint,
  FlaskConical,
  GitCompare,
  LayoutDashboard,
  type LucideIcon,
  TrendingUp,
  UserCog,
  UsersRound,
} from "lucide-react"
import { getLogTableLabel, LOG_TABLES, type LogGroup } from "./log-tables"

export type AdminNavItem = { href: string; label: string; icon: LucideIcon }
export type AdminNavGroup = { group: string; items: AdminNavItem[] }

type AdminNavT = (key: string) => string
type LogTableT = (key: string) => string

/** Built per request because entries depend on the active translations and locale. */
/** Hrefs embed the locale directly since AdminNavBar compares them against usePathname. */
export function getAdminNav(
  t: AdminNavT,
  logTableT: LogTableT,
  locale: string
): AdminNavGroup[] {
  const analyticsGroup: AdminNavGroup = {
    group: t("groups.analytics"),
    items: [
      {
        href: `/${locale}/admin`,
        label: t("items.overview"),
        icon: LayoutDashboard,
      },
      {
        href: `/${locale}/admin/ab`,
        label: t("items.abEffect"),
        icon: GitCompare,
      },
      {
        href: `/${locale}/admin/cohort`,
        label: t("items.cohort"),
        icon: UsersRound,
      },
      {
        href: `/${locale}/admin/identifier`,
        label: t("items.identifier"),
        icon: Fingerprint,
      },
      {
        href: `/${locale}/admin/tk`,
        label: t("items.tkLaw"),
        icon: TrendingUp,
      },
    ],
  }

  function buildLogGroup(groupId: LogGroup, groupLabel: string): AdminNavGroup {
    return {
      group: groupLabel,
      items: LOG_TABLES.filter((lt) => lt.group === groupId).map((lt) => ({
        href: `/${locale}/admin/logs/${lt.slug}`,
        label: getLogTableLabel(logTableT, lt.slug),
        icon: lt.icon,
      })),
    }
  }

  const logsGroup = buildLogGroup("logs", t("groups.logs"))
  const sessionsGroup = buildLogGroup("sessions", t("groups.sessions"))
  const progressGroup = buildLogGroup("progress", t("groups.progress"))

  const consentsItems: AdminNavItem[] = LOG_TABLES.filter(
    (lt) => lt.slug === "consents"
  ).map((lt) => ({
    href: `/${locale}/admin/logs/${lt.slug}`,
    label: getLogTableLabel(logTableT, lt.slug),
    icon: lt.icon,
  }))

  const accessGroup: AdminNavGroup = {
    group: t("groups.access"),
    items: [
      {
        href: `/${locale}/admin/users`,
        label: t("items.users"),
        icon: UserCog,
      },
      ...consentsItems,
    ],
  }

  const managementGroup: AdminNavGroup = {
    group: t("groups.management"),
    items: [
      {
        href: `/${locale}/admin/labs`,
        label: t("items.labs"),
        icon: FlaskConical,
      },
    ],
  }

  return [
    analyticsGroup,
    logsGroup,
    sessionsGroup,
    progressGroup,
    managementGroup,
    accessGroup,
  ]
}
