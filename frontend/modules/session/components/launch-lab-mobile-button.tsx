"use client"

import { LogInIcon, RocketIcon } from "lucide-react"
import Link from "next/link"
import { LaunchLabConfirmTrigger } from "./launch-lab-confirm-trigger"
import { authClient } from "@/auth/client"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"
import { Skeleton } from "@/ui/skeleton"

export function LaunchLabMobileButton({
  labSlug,
  returnTo,
  className,
}: {
  labSlug: string
  returnTo: string
  className?: string
}) {
  const { data, isPending } = authClient.useSession()

  if (isPending) {
    return <Skeleton className={cn("h-9 w-48", className)} />
  }

  if (!data?.user) {
    return (
      <Button
        nativeButton={false}
        className={cn("w-fit", className)}
        render={
          <Link href={`/sign-in?redirect=${encodeURIComponent(returnTo)}`} />
        }
      >
        <LogInIcon data-icon="inline-start" />
        Войти, чтобы запустить
      </Button>
    )
  }

  return (
    <LaunchLabConfirmTrigger labSlug={labSlug}>
      <Button className={cn("w-fit", className)}>
        <RocketIcon data-icon="inline-start" />
        Запустить лабораторию
      </Button>
    </LaunchLabConfirmTrigger>
  )
}
