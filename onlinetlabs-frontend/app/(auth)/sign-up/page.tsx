import type { Metadata } from "next"
import { RegisterForm } from "@/features/auth"

export const metadata: Metadata = {
  title: "Sign Up",
}

export default function SignUpPage() {
  return <RegisterForm />
}
