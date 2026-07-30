"use client"

import { Button } from "@repo/design-system/ui/button"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTranslations } from "next-intl"

export function SignInButton({
  appUrl = "",
  locale,
  redirectTo,
}: {
  /** Origin prefix for when /sign-in lives outside the app rendering this button. */
  appUrl?: string
  /** Passed explicitly because the package is locale-agnostic. */
  locale: string
  /** Absolute URL for ?redirect= when the current pathname belongs to another origin. */
  redirectTo?: string
}) {
  const t = useTranslations("shared.signInButton")
  const pathname = usePathname()
  const target = redirectTo ?? pathname

  return (
    <Button
      nativeButton={false}
      variant="link"
      render={
        <Link
          href={`${appUrl}/${locale}/sign-in?redirect=${encodeURIComponent(target)}`}
        />
      }
    >
      {t("label")}
    </Button>
  )
}
