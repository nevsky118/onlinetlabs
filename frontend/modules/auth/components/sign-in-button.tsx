"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/ui/button"

export function SignInButton() {
  const pathname = usePathname()

  return (
    <Button
      nativeButton={false}
      variant="link"
      render={
        <Link href={`/sign-in?redirect=${encodeURIComponent(pathname)}`} />
      }
    >
      Войти
    </Button>
  )
}
