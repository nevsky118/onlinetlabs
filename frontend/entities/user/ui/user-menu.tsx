"use client"

import { LogOut } from "lucide-react"
import { useRouter } from "next/navigation"
import { authClient } from "@/shared/auth/client"
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

  const handleSignOut = async () => {
    await authClient.signOut({
      fetchOptions: {
        onSuccess: () => router.refresh(),
      },
    })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className="rounded-full data-[state=open]:border-ring data-[state=open]:ring-ring/50 data-[state=open]:ring-[3px]"
        >
          <Avatar className="h-8 w-8 rounded-full">
            <AvatarImage src={user.image ?? undefined} alt={user.name ?? ""} />
            <AvatarFallback className="rounded-full">
              {getInitials(user.name)}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
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
          <DropdownMenuItem disabled>Account</DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={handleSignOut}>
          Log out
          <LogOut className="ml-auto" />
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
