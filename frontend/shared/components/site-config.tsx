"use client"

import { GalleryHorizontalIcon } from "lucide-react"
import type * as React from "react"
import { useLayout } from "@/hooks/use-layout"
import { trackCustom } from "@/lib/analytics"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"

export function SiteConfig({ className }: React.ComponentProps<typeof Button>) {
  const { layout, setLayout } = useLayout()

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => {
        const newLayout = layout === "fixed" ? "full" : "fixed"
        setLayout(newLayout)
        trackCustom("set_layout", { layout: newLayout })
      }}
      className={cn("size-8", className)}
      title="Переключить макет"
    >
      <span className="sr-only">Переключить макет</span>
      <GalleryHorizontalIcon />
    </Button>
  )
}
