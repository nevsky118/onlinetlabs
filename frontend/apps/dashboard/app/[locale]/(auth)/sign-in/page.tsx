import type { Metadata } from "next"
import { setRequestLocale } from "next-intl/server"
import { Suspense } from "react"
import { LoginForm } from "@/modules/auth"

export const metadata: Metadata = {
  title: "Sign In",
}

export default async function SignInPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)

  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  )
}
