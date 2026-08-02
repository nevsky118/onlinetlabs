"use client"

import { Button } from "@repo/design-system/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@repo/design-system/ui/dropdown-menu"
import { LanguagesIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { useTransition } from "react"
import { usePathname, useRouter } from "../navigation"
import { routing } from "../routing"

/** Endonyms, so each language is readable to its own speakers. */
const LOCALE_NAMES: Record<string, string> = {
  ru: "Русский",
  en: "English",
}

export function LocaleSwitcher() {
  const t = useTranslations("shared.localeSwitcher")
  const activeLocale = useLocale()
  const pathname = usePathname()
  const router = useRouter()
  const [isPending, startTransition] = useTransition()

  function switchTo(locale: string) {
    if (locale === activeLocale) return
    // Not useSearchParams: it would make the static marketing pages dynamic.
    const search = typeof window === "undefined" ? "" : window.location.search
    startTransition(() => router.replace(`${pathname}${search}`, { locale }))
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            size="icon"
            className="extend-touch-target size-8"
            disabled={isPending}
          />
        }
      >
        <LanguagesIcon />
        <span className="sr-only">{t("label")}</span>
      </DropdownMenuTrigger>
      {/* w-auto: the default is the anchor width, here a 32px icon button. */}
      <DropdownMenuContent align="end" className="w-auto">
        <DropdownMenuRadioGroup
          value={activeLocale}
          onValueChange={(value) => switchTo(String(value))}
        >
          {routing.locales.map((locale) => (
            <DropdownMenuRadioItem key={locale} value={locale}>
              {LOCALE_NAMES[locale] ?? locale}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
