import type { Metadata } from "next"
import { Suspense } from "react"
import { LoginForm } from "@/modules/auth"

export const metadata: Metadata = {
  title: "Sign In",
}

export default function SignInPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  )
}
