"use client"

import { authClient } from "@repo/auth/client"
import { Button } from "@repo/design-system/ui/button"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { Link } from "@repo/i18n/navigation"
import { ArrowRightIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { LaunchLabConfirmTrigger } from "./launch-lab-confirm-trigger"

export function LaunchLabCard({
  labSlug,
  returnTo,
}: {
  labSlug: string
  returnTo: string
}) {
  const t = useTranslations("dashboard.session.launchLabCard")
  const { data, isPending } = authClient.useSession()
  const isAuthed = !!data?.user

  if (isPending) {
    return (
      <div className="bg-surface flex flex-col gap-2 rounded-lg p-6">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="mt-2 h-7 w-24" />
      </div>
    )
  }

  return (
    <div className="bg-surface text-surface-foreground flex flex-col gap-2 rounded-lg p-6">
      <div className="text-base leading-tight font-semibold text-balance">
        {isAuthed ? t("title") : t("signInTitle")}
      </div>
      <div className="text-muted-foreground text-sm">
        {isAuthed ? t("description") : t("signInDescription")}
      </div>
      {isAuthed ? (
        <LaunchLabConfirmTrigger labSlug={labSlug}>
          <Button
            variant="outline"
            size="sm"
            className="mt-2 h-7 w-fit px-2.5 text-[0.8rem]"
          >
            {t("launch")}
            <ArrowRightIcon data-icon="inline-end" />
          </Button>
        </LaunchLabConfirmTrigger>
      ) : (
        <Button
          nativeButton={false}
          variant="outline"
          size="sm"
          className="mt-2 h-7 w-fit px-2.5 text-[0.8rem]"
          render={
            <Link href={`/sign-in?redirect=${encodeURIComponent(returnTo)}`} />
          }
        >
          {t("signIn")}
          <ArrowRightIcon data-icon="inline-end" />
        </Button>
      )}
    </div>
  )
}
