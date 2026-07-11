"use client"

import { GraduationCap, LogOut, Settings } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { fetchInstructorAccess } from "@/auth/actions"
import { authClient } from "@/auth/client"
import { Avatar, AvatarFallback, AvatarImage } from "@/ui/avatar"
import { Button } from "@/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/ui/dropdown-menu"

function getInitials(name?: string | null): string {
  if (!name) return "?"
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

interface UserMenuProps {
  user: {
    name: string | null
    email: string
    image: string | null
  }
}

export function UserMenu({ user }: UserMenuProps) {
  const router = useRouter()
  // Роль достоверна только на backend (better-auth тут на in-memory адаптере),
  // поэтому доступ к кабинету спрашиваем серверным экшеном.
  const [isInstructor, setIsInstructor] = useState(false)
  useEffect(() => {
    fetchInstructorAccess()
      .then(setIsInstructor)
      .catch(() => setIsInstructor(false))
  }, [])

  const handleSignOut = async () => {
    await authClient.signOut({
      fetchOptions: {
        onSuccess: () => router.refresh(),
      },
    })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            size="icon-sm"
            className="rounded-full data-popup-open:border-ring data-popup-open:ring-ring/50 data-popup-open:ring-[3px]"
          />
        }
      >
        <Avatar className="h-8 w-8 rounded-full">
          <AvatarImage src={user.image ?? undefined} alt={user.name ?? ""} />
          <AvatarFallback className="rounded-full">
            {getInitials(user.name)}
          </AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-(--anchor-width) min-w-56 rounded-none"
        side="bottom"
        align="end"
        sideOffset={4}
      >
        <DropdownMenuLabel className="p-0 font-normal">
          <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
            <Avatar className="h-8 w-8 rounded-full">
              <AvatarImage
                src={user.image ?? undefined}
                alt={user.name ?? ""}
              />
              <AvatarFallback className="rounded-full">
                {getInitials(user.name)}
              </AvatarFallback>
            </Avatar>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium">{user.name}</span>
              <span className="truncate text-xs">{user.email}</span>
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          {isInstructor ? (
            <DropdownMenuItem render={<Link href="/instructor" />}>
              Кабинет преподавателя
              <GraduationCap className="ml-auto" />
            </DropdownMenuItem>
          ) : null}
          <DropdownMenuItem render={<Link href="/settings" />}>
            Настройки
            <Settings className="ml-auto" />
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={handleSignOut}>
          Выйти
          <LogOut className="ml-auto" />
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
