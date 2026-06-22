"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const tabs = [
  { href: "/admin", label: "Обзор" },
  { href: "/admin/ab", label: "A/B-эффект" },
  { href: "/admin/cohort", label: "Когорта" },
  { href: "/admin/identifier", label: "Идентификатор" },
  { href: "/admin/tk", label: "Закон T_k" },
  { href: "/admin/users", label: "Пользователи" },
]

export function AdminTabs() {
  const pathname = usePathname()

  return (
    <nav className="-mb-px flex gap-1 overflow-x-auto border-b">
      {tabs.map((tab) => {
        const active =
          tab.href === "/admin"
            ? pathname === "/admin"
            : pathname.startsWith(tab.href)
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={cn(
              "shrink-0 border-b-2 px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors",
              active
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {tab.label}
          </Link>
        )
      })}
    </nav>
  )
}
