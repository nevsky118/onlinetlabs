"use client"

import { authClient } from "@repo/auth/client"
import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { Link } from "@repo/i18n/navigation"
import { LogInIcon, RocketIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { LaunchLabConfirmTrigger } from "./launch-lab-confirm-trigger"

export function LaunchLabMobileButton({
  labSlug,
  returnTo,
  className,
}: {
  labSlug: string
  returnTo: string
  className?: string
}) {
  const t = useTranslations("dashboard.session.launchLabMobileButton")
  const { data, isPending } = authClient.useSession()

  if (isPending) {
    return <Skeleton className={cn("h-9 w-48", className)} />
  }

  if (!data?.user) {
    return (
      <Button
        nativeButton={false}
        className={cn("w-fit", className)}
        render={
          <Link href={`/sign-in?redirect=${encodeURIComponent(returnTo)}`} />
        }
      >
        <LogInIcon data-icon="inline-start" />
        {t("signInToLaunch")}
      </Button>
    )
  }

  return (
    <LaunchLabConfirmTrigger labSlug={labSlug}>
      <Button className={cn("w-fit", className)}>
        <RocketIcon data-icon="inline-start" />
        {t("launchLab")}
      </Button>
    </LaunchLabConfirmTrigger>
  )
}
