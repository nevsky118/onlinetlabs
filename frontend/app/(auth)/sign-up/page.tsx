import type { Metadata } from "next"
import { Suspense } from "react"
import { RegisterForm } from "@/modules/auth"

export const metadata: Metadata = {
  title: "Sign Up",
}

export default function SignUpPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  )
}
