"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/ui/button"

export function SignInButton() {
  const pathname = usePathname()

  return (
    <Button asChild variant="link">
      <Link href={`/sign-in?redirect=${encodeURIComponent(pathname)}`}>
        Sign In
      </Link>
    </Button>
  )
}
