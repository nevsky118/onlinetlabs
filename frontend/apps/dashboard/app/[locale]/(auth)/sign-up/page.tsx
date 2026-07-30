import type { Metadata } from "next"
import { setRequestLocale } from "next-intl/server"
import { Suspense } from "react"
import { RegisterForm } from "@/modules/auth"

export const metadata: Metadata = {
  title: "Sign Up",
}

export default async function SignUpPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  setRequestLocale(locale)

  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  )
}
