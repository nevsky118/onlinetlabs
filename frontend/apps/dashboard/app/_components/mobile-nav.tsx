"use client"

import { getDashboardDestinations } from "@/lib/config"
import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@repo/design-system/ui/popover"
import { useLocale, useTranslations } from "next-intl"
import Link, { type LinkProps } from "next/link"
import { useRouter } from "next/navigation"
import * as React from "react"

export function MobileNav({
  items,
  className,
}: {
  items: { href: string; label: string }[]
  className?: string
}) {
  const [open, setOpen] = React.useState(false)
  const t = useTranslations("dashboard.app.mobileNav")
  const locale = useLocale()
  const dashboardDestinations = React.useMemo(
    () => getDashboardDestinations(t, locale),
    [t, locale]
  )

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        render={
          <Button
            variant="ghost"
            className={cn(
              "extend-touch-target h-8 touch-manipulation items-center justify-start gap-2.5 !p-0 hover:bg-transparent focus-visible:bg-transparent focus-visible:ring-0 active:bg-transparent dark:hover:bg-transparent",
              className
            )}
          />
        }
      >
        <div className="relative flex h-8 w-4 items-center justify-center">
          <div className="relative size-4">
            <span
              className={cn(
                "absolute left-0 block h-0.5 w-4 bg-foreground transition-all duration-100",
                open ? "top-[0.4rem] -rotate-45" : "top-1"
              )}
            />
            <span
              className={cn(
                "absolute left-0 block h-0.5 w-4 bg-foreground transition-all duration-100",
                open ? "top-[0.4rem] rotate-45" : "top-2.5"
              )}
            />
          </div>
          <span className="sr-only">{t("openMenu")}</span>
        </div>
        <span className="flex h-8 items-center text-lg leading-none font-medium">
          {t("menuLabel")}
        </span>
      </PopoverTrigger>
      <PopoverContent
        className="no-scrollbar h-(--available-height) w-(--available-width) overflow-y-auto rounded-none border-none bg-background/90 p-0 shadow-none backdrop-blur duration-100"
        align="start"
        side="bottom"
        alignOffset={-16}
        sideOffset={14}
      >
        <div className="flex flex-col gap-12 overflow-auto px-6 py-6">
          <div className="flex flex-col gap-4">
            <div className="text-sm font-medium text-muted-foreground">
              {t("menuLabel")}
            </div>
            <div className="flex flex-col gap-3">
              <MobileLink href={`/${locale}`} onOpenChange={setOpen}>
                {t("home")}
              </MobileLink>
              {items.map((item) => (
                <MobileLink
                  key={item.href}
                  href={item.href}
                  onOpenChange={setOpen}
                >
                  {item.label}
                </MobileLink>
              ))}
            </div>
          </div>
          <div className="flex flex-col gap-4">
            <div className="text-sm font-medium text-muted-foreground">
              {t("sectionsHeading")}
            </div>
            <div className="flex flex-col gap-3">
              {dashboardDestinations.map(({ name, href }) => (
                <MobileLink key={href} href={href} onOpenChange={setOpen}>
                  {name}
                </MobileLink>
              ))}
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

function MobileLink({
  href,
  onOpenChange,
  className,
  children,
  ...props
}: LinkProps & {
  onOpenChange?: (open: boolean) => void
  children: React.ReactNode
  className?: string
}) {
  const router = useRouter()
  return (
    <Link
      href={href}
      onClick={() => {
        router.push(href.toString())
        onOpenChange?.(false)
      }}
      className={cn("text-2xl font-medium", className)}
      {...props}
    >
      {children}
    </Link>
  )
}
