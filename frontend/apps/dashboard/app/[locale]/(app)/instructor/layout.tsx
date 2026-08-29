import { NextIntlClientProvider } from "next-intl"
import { setRequestLocale } from "next-intl/server"
import { instructorMessages } from "@/lib/messages"

export default async function InstructorLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)

  return (
    <NextIntlClientProvider messages={await instructorMessages(locale)}>
      {children}
    </NextIntlClientProvider>
  )
}
