import Link from "next/link"
import { Suspense } from "react"
import { CommandMenu } from "@/components/command-menu"
import { Icons } from "@/components/icons"
import { MainNav } from "@/components/main-nav"
import { MobileNav } from "@/components/mobile-nav"
import { SiteConfig } from "@/components/site-config"
import { ThemeSwitcher } from "@/components/theme-switcher"
import { UserMenu } from "@/entities/user/ui/user-menu"
import { SignInButton } from "@/features/auth/ui/sign-in-button"
import { siteConfig } from "@/lib/config"
import { course, labs } from "@/lib/source"
import { getSession } from "@/shared/auth/session"
import { Button } from "@/ui/button"
import { Separator } from "@/ui/separator"

export function SiteHeader() {
  const coursesPageTree = course.pageTree
  const labsPageTree = labs.pageTree

  return (
    <header className="bg-background sticky top-0 z-50 w-full">
      <div className="container-wrapper 3xl:fixed:px-0 px-6">
        <div className="3xl:fixed:container flex h-(--header-height) items-center gap-2 **:data-[slot=separator]:h-4!">
          <MobileNav
            tree={coursesPageTree}
            items={siteConfig.navItems}
            className="flex lg:hidden"
          />
          <Button
            asChild
            variant="ghost"
            size="icon"
            className="hidden size-8 lg:flex"
          >
            <Link href="/">
              <Icons.logo className="size-5" />
              <span className="sr-only">{siteConfig.name}</span>
            </Link>
          </Button>
          <MainNav items={siteConfig.navItems} className="hidden lg:flex" />
          <div className="ml-auto flex items-center gap-2 md:flex-1 md:justify-end">
            <div className="hidden w-full flex-1 md:flex md:w-auto md:flex-none">
              <CommandMenu
                trees={[
                  { tree: coursesPageTree, label: "Courses" },
                  { tree: labsPageTree, label: "Labs" },
                ]}
                navItems={siteConfig.navItems}
              />
            </div>
            <Separator orientation="vertical" className="3xl:flex hidden" />
            <SiteConfig className="3xl:flex hidden" />
            <Separator orientation="vertical" />
            <ThemeSwitcher />
            <Suspense>
              <AuthStatus />
            </Suspense>
          </div>
        </div>
      </div>
    </header>
  )
}

async function AuthStatus() {
  const session = await getSession()

  if (!session) return <SignInButton />

  return (
    <UserMenu
      user={{
        name: session.user.name,
        email: session.user.email,
        image: session.user.image ?? null,
      }}
    />
  )
}
