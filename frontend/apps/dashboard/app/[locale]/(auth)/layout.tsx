import { NextIntlClientProvider } from "next-intl"
import { setRequestLocale } from "next-intl/server"
import { authMessages } from "@/lib/messages"

export default async function AuthLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)

  return (
    <NextIntlClientProvider messages={await authMessages(locale)}>
      <div className="bg-background flex min-h-svh items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </NextIntlClientProvider>
  )
}
