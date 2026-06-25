"use client"

import { ChevronDown } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useLayoutEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"
import { ADMIN_NAV, type AdminNavItem } from "@/modules/admin/lib/admin-nav"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/ui/dropdown-menu"

const HOME = "/admin"

function isActive(pathname: string, href: string): boolean {
  return href === HOME ? pathname === HOME : pathname.startsWith(href)
}

const tabBase =
  "group/tab relative flex h-12 shrink-0 cursor-pointer items-center gap-2 whitespace-nowrap px-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-inset"
const tabIdle =
  "text-muted-foreground hover:bg-foreground/[0.04] hover:text-foreground"
const tabActive = "text-foreground"

function TabIcon({ icon: Icon }: { icon: AdminNavItem["icon"] }) {
  return (
    <Icon
      className="size-4 shrink-0 opacity-60 transition-opacity group-hover/tab:opacity-100 group-data-[active=true]/tab:opacity-100"
      aria-hidden
    />
  )
}

function NavTab({ item, active }: { item: AdminNavItem; active: boolean }) {
  return (
    <Link
      href={item.href}
      data-active={active}
      aria-current={active ? "page" : undefined}
      className={cn(tabBase, active ? tabActive : tabIdle)}
    >
      <TabIcon icon={item.icon} />
      {item.label}
    </Link>
  )
}

function NavGroup({
  label,
  items,
  pathname,
  active,
}: {
  label: string
  items: AdminNavItem[]
  pathname: string
  active: boolean
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        data-active={active}
        className={cn(tabBase, active ? tabActive : tabIdle)}
      >
        {label}
        <ChevronDown
          className="size-3.5 shrink-0 opacity-50 transition-transform duration-200 group-data-[state=open]/tab:rotate-180"
          aria-hidden
        />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" sideOffset={0} className="w-56">
        <DropdownMenuGroup>
          {items.map((item) => {
            const Icon = item.icon
            return (
              <DropdownMenuItem
                key={item.href}
                asChild
                data-active={isActive(pathname, item.href)}
                className="data-[active=true]:bg-foreground data-[active=true]:text-background"
              >
                <Link href={item.href}>
                  <Icon className="size-4" aria-hidden />
                  {item.label}
                </Link>
              </DropdownMenuItem>
            )
          })}
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export function AdminNavBar(): React.JSX.Element {
  const pathname = usePathname()
  const rowRef = useRef<HTMLDivElement>(null)
  const [ind, setInd] = useState({
    left: 0,
    width: 0,
    ready: false,
    animate: false,
  })

  // biome-ignore lint/correctness/useExhaustiveDependencies: re-measure active tab on route change
  useLayoutEffect(() => {
    const row = rowRef.current
    if (!row) return

    function measure() {
      if (!row) return
      const el = row.querySelector<HTMLElement>('[data-active="true"]')
      if (!el) {
        setInd((s) => ({ ...s, ready: false }))
        return
      }
      setInd((prev) => ({
        left: el.offsetLeft,
        width: el.offsetWidth,
        ready: true,
        animate: prev.ready,
      }))
    }

    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(row)
    window.addEventListener("resize", measure)
    return () => {
      ro.disconnect()
      window.removeEventListener("resize", measure)
    }
  }, [pathname])

  const allItems = ADMIN_NAV.flatMap((g) => g.items)
  const home = allItems.find((i) => i.href === HOME)

  return (
    <div className="border-grid sticky top-(--header-height) z-30 border-b bg-background/70 backdrop-blur-md">
      <div className="container-wrapper">
        <div className="container flex h-12 items-center gap-2">
          <span className="hidden shrink-0 select-none bg-foreground px-1.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-background sm:inline-block">
            Админ
          </span>
          <div className="hidden h-5 w-px shrink-0 bg-border sm:block" />
          <div
            ref={rowRef}
            className="no-scrollbar relative flex h-12 flex-1 items-center gap-0.5 overflow-x-auto"
          >
            {home && (
              <NavTab item={home} active={isActive(pathname, home.href)} />
            )}
            {ADMIN_NAV.map((group) => {
              const items = group.items.filter((i) => i.href !== HOME)
              const single = items[0]
              if (!single) return null
              if (items.length === 1) {
                return (
                  <NavTab
                    key={single.href}
                    item={single}
                    active={isActive(pathname, single.href)}
                  />
                )
              }
              const groupActive = items.some((i) => isActive(pathname, i.href))
              return (
                <NavGroup
                  key={group.group}
                  label={group.group}
                  items={items}
                  pathname={pathname}
                  active={groupActive}
                />
              )
            })}
            <span
              aria-hidden
              style={{
                left: ind.left,
                width: ind.width,
                opacity: ind.ready ? 1 : 0,
              }}
              className={cn(
                "pointer-events-none absolute bottom-0 h-0.5 bg-foreground transition-opacity duration-200",
                ind.animate &&
                  "transition-[left,width,opacity] duration-300 ease-out"
              )}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
