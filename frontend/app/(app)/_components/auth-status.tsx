"use client"

import { authClient } from "@/auth/client"
import { SignInButton, UserMenu } from "@/modules/auth"
import { Skeleton } from "@/ui/skeleton"

// Статус входа читаем на клиенте: каталог/лабы — force-static, серверный getSession там пуст (показал бы Войти залогиненному).
export function AuthStatus() {
  const { data, isPending } = authClient.useSession()

  if (isPending) {
    return <Skeleton className="size-8 rounded-full" />
  }

  if (!data?.user) {
    return <SignInButton />
  }

  return (
    <UserMenu
      user={{
        name: data.user.name,
        email: data.user.email,
        image: data.user.image ?? null,
      }}
    />
  )
}
