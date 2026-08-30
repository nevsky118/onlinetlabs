"use client"

import { useIsHydrated } from "@repo/design-system/hooks/use-is-hydrated"
import { cn } from "@repo/design-system/lib/utils"
import { useTranslations } from "next-intl"
import { useTheme } from "next-themes"

const THEME_VALUES = ["light", "dark", "system"] as const

export function ThemeControl() {
  const t = useTranslations("dashboard.settings")
  const { theme, setTheme } = useTheme()
  const isHydrated = useIsHydrated()
  const current = isHydrated ? (theme ?? "system") : "system"

  return (
    <div className="inline-flex border border-border">
      {THEME_VALUES.map((value, index) => (
        <button
          key={value}
          type="button"
          onClick={() => setTheme(value)}
          className={cn(
            "px-3 py-1.5 text-sm transition-colors focus-visible:ring-1 focus-visible:ring-ring focus-visible:outline-none focus-visible:ring-inset",
            index > 0 && "border-l border-border",
            current === value
              ? "bg-foreground font-medium text-background"
              : "text-muted-foreground hover:bg-foreground/[0.06] hover:text-foreground"
          )}
        >
          {t(`themes.${value}`)}
        </button>
      ))}
    </div>
  )
}
