import { appMessages } from "@/lib/messages"
import { NextIntlClientProvider } from "next-intl"
import { setRequestLocale } from "next-intl/server"
import { SiteFooter } from "./_components/site-footer"
import { SiteHeader } from "./_components/site-header"

export default async function AppLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)

  return (
    <NextIntlClientProvider messages={await appMessages(locale)}>
      <div
        data-slot="layout"
        className="relative z-10 flex min-h-svh flex-col bg-background"
      >
        <SiteHeader />
        <main className="flex flex-1 flex-col">{children}</main>
        <SiteFooter />
      </div>
    </NextIntlClientProvider>
  )
}
