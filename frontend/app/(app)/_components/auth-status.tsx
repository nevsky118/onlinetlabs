"use client"

import { authClient } from "@/auth/client"
import { SignInButton, UserMenu } from "@/modules/auth"
import { Skeleton } from "@/ui/skeleton"

// Статус входа читаем на клиенте через useSession. Страницы каталога и лаб
// рендерятся как force-static, поэтому серверный getSession на них всегда
// возвращает пусто и шапка показывала бы Войти даже залогиненному. Клиентский
// useSession читает сессию в браузере и работает одинаково на любой странице.
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
