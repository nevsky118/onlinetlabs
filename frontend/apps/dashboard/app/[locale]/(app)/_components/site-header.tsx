import { Icons } from "@repo/design-system/components/icons"
import { ThemeSwitcher } from "@repo/design-system/components/theme-switcher"
import { Button } from "@repo/design-system/ui/button"
import { Separator } from "@repo/design-system/ui/separator"
import Link from "next/link"
import { getLocale, getTranslations } from "next-intl/server"
import { AuthStatus } from "./auth-status"
import { CommandMenu } from "@/app-components/command-menu"
import { MainNav } from "@/app-components/main-nav"
import { MobileNav } from "@/app-components/mobile-nav"
import { SiteConfig } from "@/app-components/site-config"
import { getNavItems } from "@/lib/config"

export async function SiteHeader() {
  const [navT, siteT, themeT, locale] = await Promise.all([
    getTranslations("dashboard.app.nav"),
    getTranslations("dashboard.app.site"),
    getTranslations("dashboard.app.themeSwitcher"),
    getLocale(),
  ])
  const navItems = getNavItems(navT, locale)

  return (
    <header className="bg-background sticky top-0 z-50 w-full">
      <div className="container-wrapper 3xl:fixed:px-0 px-6">
        <div className="3xl:fixed:container flex h-(--header-height) items-center gap-2 **:data-[slot=separator]:h-4! **:data-[slot=separator]:self-center">
          <MobileNav items={navItems} className="flex lg:hidden" />
          <Button
            nativeButton={false}
            variant="ghost"
            size="icon"
            className="hidden size-8 lg:flex"
            render={<Link href={`/${locale}`} />}
          >
            <Icons.logo className="size-5" />
            <span className="sr-only">{siteT("name")}</span>
          </Button>
          <MainNav items={navItems} className="hidden lg:flex" />
          <div className="ml-auto flex items-center gap-2 md:flex-1 md:justify-end">
            <div className="hidden w-full flex-1 md:flex md:w-auto md:flex-none">
              <CommandMenu navItems={navItems} />
            </div>
            <Separator orientation="vertical" className="3xl:flex hidden" />
            <SiteConfig className="3xl:flex hidden" />
            <Separator orientation="vertical" />
            <ThemeSwitcher labelToggleTheme={themeT("toggle")} />
            <AuthStatus />
          </div>
        </div>
      </div>
    </header>
  )
}
