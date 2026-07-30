"use client"

import { authClient } from "@repo/auth/client"
import { SignInButton } from "@repo/auth/components/sign-in-button"
import { UserMenu } from "@repo/auth/components/user-menu"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { useLocale } from "next-intl"
import { useEffect, useState } from "react"
import { fetchInstructorAccess } from "./instructor-access"

// We read the sign-in status on the client. The catalog and labs are force-static, so the server-side getSession is empty there (it would show Sign in to a logged-in user).
export function AuthStatus() {
  const { data, isPending } = authClient.useSession()
  const locale = useLocale()
  // Role is only trustworthy on the backend, better-auth runs on an in-memory adapter here,
  // so instructor access comes from a server action
  const [isInstructor, setIsInstructor] = useState(false)
  // biome-ignore lint/correctness/useExhaustiveDependencies: keyed on the user id so a new session object does not refetch
  useEffect(() => {
    if (!data?.user) return
    fetchInstructorAccess()
      .then(setIsInstructor)
      .catch(() => setIsInstructor(false))
  }, [data?.user?.id])

  if (isPending) {
    return <Skeleton className="size-8 rounded-full" />
  }

  if (!data?.user) {
    return <SignInButton locale={locale} />
  }

  return (
    <UserMenu
      user={{
        name: data.user.name,
        email: data.user.email,
        image: data.user.image ?? null,
      }}
      instructorAccess={isInstructor}
      locale={locale}
    />
  )
}
