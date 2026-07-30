import { redirect } from "@repo/i18n/navigation"
import { setRequestLocale } from "next-intl/server"

/** The dashboard has no public landing page. The logo and the post-login redirect both land here. */
export default async function RootPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)
  redirect({ href: "/sessions", locale })
}
