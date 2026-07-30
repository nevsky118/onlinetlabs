import { Icons } from "@repo/design-system/components/icons"
import { ThemeSwitcher } from "@repo/design-system/components/theme-switcher"
import { Button } from "@repo/design-system/ui/button"
import { Separator } from "@repo/design-system/ui/separator"
import type { Root as FumaDocsPageTree } from "fumadocs-core/page-tree"
import Link from "next/link"
import { getLocale, getTranslations } from "next-intl/server"
import { AuthStatus } from "./auth-status"
import { CommandMenu } from "@/app-components/command-menu"
import { MainNav } from "@/app-components/main-nav"
import { MobileNav } from "@/app-components/mobile-nav"
import { SiteConfig } from "@/app-components/site-config"
import { getNavItems } from "@/lib/config"

export async function SiteHeader({
  searchTree,
  navTree,
}: {
  // Tree for CommandMenu, courses and labs merged
  searchTree?: FumaDocsPageTree
  // Tree for MobileNav, courses only
  navTree?: FumaDocsPageTree
} = {}) {
  const [tNav, tSite, tTheme, locale] = await Promise.all([
    getTranslations("web.nav"),
    getTranslations("web.site"),
    getTranslations("web.themeSwitcher"),
    getLocale(),
  ])
  const navItems = getNavItems(tNav, locale)

  return (
    <header className="bg-background sticky top-0 z-50 w-full">
      <div className="container-wrapper 3xl:fixed:px-0 px-6">
        <div className="3xl:fixed:container flex h-(--header-height) items-center gap-2 **:data-[slot=separator]:h-4! **:data-[slot=separator]:self-center">
          <MobileNav
            tree={navTree}
            items={navItems}
            className="flex lg:hidden"
          />
          <Button
            nativeButton={false}
            variant="ghost"
            size="icon"
            className="hidden size-8 lg:flex"
            render={<Link href={`/${locale}`} />}
          >
            <Icons.logo className="size-5" />
            <span className="sr-only">{tSite("name")}</span>
          </Button>
          <MainNav items={navItems} className="hidden lg:flex" />
          <div className="ml-auto flex items-center gap-2 md:flex-1 md:justify-end">
            <div className="hidden w-full flex-1 md:flex md:w-auto md:flex-none">
              <CommandMenu tree={searchTree} navItems={navItems} />
            </div>
            <Separator orientation="vertical" className="3xl:flex hidden" />
            <SiteConfig className="3xl:flex hidden" />
            <Separator orientation="vertical" />
            <ThemeSwitcher labelToggleTheme={tTheme("toggle")} />
            <AuthStatus />
          </div>
        </div>
      </div>
    </header>
  )
}
