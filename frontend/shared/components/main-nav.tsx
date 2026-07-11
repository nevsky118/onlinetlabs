"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"

export function MainNav({
  items,
  className,
  ...props
}: React.ComponentProps<"nav"> & {
  items: { href: string; label: string }[]
}) {
  const pathname = usePathname()

  return (
    <nav className={cn("items-center gap-0.5", className)} {...props}>
      {items.map((item) => (
        <Button
          nativeButton={false}
          key={item.href}
          variant="ghost"
          size="sm"
          render={
            <Link
              href={item.href}
              className={cn(pathname === item.href && "text-primary")}
            />
          }
        >
          {item.label}
        </Button>
      ))}
    </nav>
  )
}
