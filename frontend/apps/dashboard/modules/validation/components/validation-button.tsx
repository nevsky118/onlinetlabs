"use client"

import { Button } from "@repo/design-system/ui/button"
import { Sheet, SheetTrigger } from "@repo/design-system/ui/sheet"
import { PlayIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { ValidationSheet } from "./validation-sheet"

type Props = {
  sessionId: string
  labSlug: string
}

export function ValidationButton({ sessionId, labSlug }: Props) {
  const t = useTranslations("dashboard.validation.button")
  return (
    <Sheet>
      <SheetTrigger
        render={<Button variant="outline" size="sm" className="rounded-none" />}
      >
        <PlayIcon data-icon="inline-start" />
        {t("check")}
      </SheetTrigger>
      <ValidationSheet sessionId={sessionId} labSlug={labSlug} />
    </Sheet>
  )
}
