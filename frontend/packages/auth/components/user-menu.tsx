"use client"

import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@repo/design-system/ui/avatar"
import { Button } from "@repo/design-system/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@repo/design-system/ui/dropdown-menu"
import { GraduationCap, LogOut, Settings } from "lucide-react"
import { useTranslations } from "next-intl"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { authClient } from "../client"

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
  /** Computed by the calling app, which owns the working server action. */
  instructorAccess?: boolean
  /** Origin prefix for /instructor and /settings when the menu renders outside the app owning those routes. */
  appUrl?: string
  /** Passed explicitly because the package is locale-agnostic. */
  locale: string
}

export function UserMenu({
  user,
  instructorAccess = false,
  appUrl = "",
  locale,
}: UserMenuProps) {
  const t = useTranslations("shared.userMenu")
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
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            size="icon-sm"
            className="rounded-full data-popup-open:border-ring data-popup-open:ring-[3px] data-popup-open:ring-ring/50"
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
        {/* base-ui throws when a label or item has no group ancestor. */}
        <DropdownMenuGroup>
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
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          {instructorAccess ? (
            <DropdownMenuItem
              render={<Link href={`${appUrl}/${locale}/instructor`} />}
            >
              {t("instructor")}
              <GraduationCap className="ml-auto" />
            </DropdownMenuItem>
          ) : null}
          <DropdownMenuItem
            render={<Link href={`${appUrl}/${locale}/settings`} />}
          >
            {t("settings")}
            <Settings className="ml-auto" />
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        {/* onClick, not onSelect: onSelect type-checks as the DOM select event and never fires. */}
        <DropdownMenuGroup>
          <DropdownMenuItem onClick={handleSignOut}>
            {t("signOut")}
            <LogOut className="ml-auto" />
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
