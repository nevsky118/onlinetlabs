"use client"

import { ArrowRightIcon } from "lucide-react"
import Link from "next/link"
import { LaunchLabConfirmTrigger } from "./launch-lab-confirm-trigger"
import { authClient } from "@/auth/client"
import { Button } from "@/ui/button"
import { Skeleton } from "@/ui/skeleton"

export function LaunchLabCard({
  labSlug,
  returnTo,
}: {
  labSlug: string
  returnTo: string
}) {
  const { data, isPending } = authClient.useSession()
  const isAuthed = !!data?.user

  if (isPending) {
    return (
      <div className="bg-surface flex flex-col gap-2 rounded-lg p-6">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="mt-2 h-7 w-24" />
      </div>
    )
  }

  return (
    <div className="bg-surface text-surface-foreground flex flex-col gap-2 rounded-lg p-6">
      <div className="text-base leading-tight font-semibold text-balance">
        {isAuthed ? "Запустить лабораторию" : "Войдите, чтобы запустить"}
      </div>
      <div className="text-muted-foreground text-sm">
        {isAuthed
          ? "Выделенная среда GNS3. Запускается за несколько секунд."
          : "Нужен аккаунт — после входа сразу сможешь запустить."}
      </div>
      {isAuthed ? (
        <LaunchLabConfirmTrigger labSlug={labSlug}>
          <Button
            variant="outline"
            size="sm"
            className="mt-2 h-7 w-fit px-2.5 text-[0.8rem]"
          >
            Запустить
            <ArrowRightIcon data-icon="inline-end" />
          </Button>
        </LaunchLabConfirmTrigger>
      ) : (
        <Button
          asChild
          variant="outline"
          size="sm"
          className="mt-2 h-7 w-fit px-2.5 text-[0.8rem]"
        >
          <Link href={`/sign-in?redirect=${encodeURIComponent(returnTo)}`}>
            Войти
            <ArrowRightIcon data-icon="inline-end" />
          </Link>
        </Button>
      )}
    </div>
  )
}
