"use client"

import { appUrl, webUrl } from "@/lib/urls"
import { authClient } from "@repo/auth/client"
import { SignInButton } from "@repo/auth/components/sign-in-button"
import { UserMenu } from "@repo/auth/components/user-menu"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { useLocale } from "next-intl"
import { usePathname } from "next/navigation"

/**
 * Session is read client-side because course and lab routes are force-static, where server getSession is empty.
 * instructorAccess is not passed. Web has no server action to compute it.
 */
export function AuthStatus() {
  const { data, isPending } = authClient.useSession()
  const pathname = usePathname()
  const locale = useLocale()

  if (isPending) {
    return <Skeleton className="size-8 rounded-full" />
  }

  if (!data?.user) {
    return (
      <SignInButton
        appUrl={appUrl}
        locale={locale}
        redirectTo={`${webUrl}${pathname}`}
      />
    )
  }

  return (
    <UserMenu
      user={{
        name: data.user.name,
        email: data.user.email,
        image: data.user.image ?? null,
      }}
      appUrl={appUrl}
      locale={locale}
    />
  )
}
