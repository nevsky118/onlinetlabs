"use client"

import { PlayIcon } from "lucide-react"
import { ValidationSheet } from "./validation-sheet"
import { Button } from "@/ui/button"
import { Sheet, SheetTrigger } from "@/ui/sheet"

type Props = {
  sessionId: string
  labSlug: string
}

export function ValidationButton({ sessionId, labSlug }: Props) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="rounded-none">
          <PlayIcon data-icon="inline-start" />
          Проверить
        </Button>
      </SheetTrigger>
      <ValidationSheet sessionId={sessionId} labSlug={labSlug} />
    </Sheet>
  )
}
