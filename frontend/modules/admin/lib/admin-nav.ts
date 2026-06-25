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
import { LOG_TABLES } from "./log-tables"

export type AdminNavItem = { href: string; label: string; icon: LucideIcon }
export type AdminNavGroup = { group: string; items: AdminNavItem[] }

const analyticsGroup: AdminNavGroup = {
  group: "Аналитика",
  items: [
    { href: "/admin", label: "Обзор", icon: LayoutDashboard },
    { href: "/admin/ab", label: "A/B-эффект", icon: GitCompare },
    { href: "/admin/cohort", label: "Когорта", icon: UsersRound },
    { href: "/admin/identifier", label: "Идентификатор", icon: Fingerprint },
    { href: "/admin/tk", label: "Закон T_k", icon: TrendingUp },
  ],
}

function buildLogGroup(groupName: string): AdminNavGroup {
  return {
    group: groupName,
    items: LOG_TABLES.filter((t) => t.group === groupName).map((t) => ({
      href: `/admin/logs/${t.slug}`,
      label: t.label,
      icon: t.icon,
    })),
  }
}

const logsGroup = buildLogGroup("Логи")
const sessionsGroup = buildLogGroup("Сессии")
const progressGroup = buildLogGroup("Прогресс")

const consentsItems: AdminNavItem[] = LOG_TABLES.filter(
  (t) => t.slug === "consents"
).map((t) => ({ href: `/admin/logs/${t.slug}`, label: t.label, icon: t.icon }))

const accessGroup: AdminNavGroup = {
  group: "Доступ",
  items: [
    { href: "/admin/users", label: "Пользователи", icon: UserCog },
    ...consentsItems,
  ],
}

const managementGroup: AdminNavGroup = {
  group: "Управление",
  items: [{ href: "/admin/labs", label: "Лабы", icon: FlaskConical }],
}

export const ADMIN_NAV: AdminNavGroup[] = [
  analyticsGroup,
  logsGroup,
  sessionsGroup,
  progressGroup,
  managementGroup,
  accessGroup,
]

export const ADMIN_NAV_ITEMS: AdminNavItem[] = ADMIN_NAV.flatMap(
  (group) => group.items
)
