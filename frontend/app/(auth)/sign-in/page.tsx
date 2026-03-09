import type { Metadata } from "next"
import { LoginForm } from "@/features/auth"

export const metadata: Metadata = {
  title: "Sign In",
}

export default function SignInPage() {
  return <LoginForm />
}
