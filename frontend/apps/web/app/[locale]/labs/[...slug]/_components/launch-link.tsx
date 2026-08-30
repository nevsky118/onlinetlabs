"use client"

import { appUrl } from "@/lib/urls"
import { authClient } from "@repo/auth/client"
import { Button } from "@repo/design-system/ui/button"
import { RocketIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import Link from "next/link"

/** Cross-domain link to the dashboard, which owns lab launch and sessions. */
export function LaunchLink({ labSlug }: { labSlug: string }) {
  const t = useTranslations("web.launchLink")
  const locale = useLocale()
  const { data } = authClient.useSession()
  const href = `${appUrl}/${locale}/labs/${labSlug}/launch`

  return (
    <Button nativeButton={false} size="sm" render={<Link href={href} />}>
      <RocketIcon data-icon="inline-start" />
      {data?.user ? t("launch") : t("signInAndLaunch")}
    </Button>
  )
}
