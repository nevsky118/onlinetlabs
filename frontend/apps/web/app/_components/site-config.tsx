"use client"

import { trackCustom } from "@repo/api/analytics"
import { useLayout } from "@repo/design-system/hooks/use-layout"
import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import { GalleryHorizontalIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import type * as React from "react"

export function SiteConfig({ className }: React.ComponentProps<typeof Button>) {
  const { layout, setLayout } = useLayout()
  const t = useTranslations("web.siteConfig")

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
      title={t("toggleLayout")}
    >
      <span className="sr-only">{t("toggleLayout")}</span>
      <GalleryHorizontalIcon />
    </Button>
  )
}
