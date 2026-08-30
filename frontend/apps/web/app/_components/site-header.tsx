import { CommandMenu } from "@/app-components/command-menu"
import { MainNav } from "@/app-components/main-nav"
import { MobileNav } from "@/app-components/mobile-nav"
import { SiteConfig } from "@/app-components/site-config"
import { getNavItems } from "@/lib/config"
import { Icons } from "@repo/design-system/components/icons"
import { ThemeSwitcher } from "@repo/design-system/components/theme-switcher"
import { Button } from "@repo/design-system/ui/button"
import { Separator } from "@repo/design-system/ui/separator"
import { LocaleSwitcher } from "@repo/i18n/components/locale-switcher"
import { getLocale, getTranslations } from "next-intl/server"
import Link from "next/link"
import type { Root as FumaDocsPageTree } from "fumadocs-core/page-tree"
import { AuthStatus } from "./auth-status"

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
    <header className="sticky top-0 z-50 w-full bg-background">
      <div className="container-wrapper px-6 3xl:fixed:px-0">
        <div className="flex h-(--header-height) items-center gap-2 **:data-[slot=separator]:h-4! **:data-[slot=separator]:self-center 3xl:fixed:container">
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
            <Separator orientation="vertical" className="hidden 3xl:flex" />
            <SiteConfig className="hidden 3xl:flex" />
            <Separator orientation="vertical" />
            <ThemeSwitcher labelToggleTheme={tTheme("toggle")} />
            <LocaleSwitcher />
            <AuthStatus />
          </div>
        </div>
      </div>
    </header>
  )
}
