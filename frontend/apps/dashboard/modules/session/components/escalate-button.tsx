"use client"

import { Button } from "@repo/design-system/ui/button"
import { LifeBuoyIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

export function EscalateButton({ sessionId }: { sessionId: string }) {
  const t = useTranslations("dashboard.session.escalateButton")
  const [pending, setPending] = useState(false)

  async function handleClick() {
    setPending(true)
    try {
      const r = await fetch(`/api/sessions/${sessionId}/escalate`, {
        method: "POST",
      })
      if (!r.ok) throw new Error(`${r.status}`)
      toast.success(t("toastSent"))
    } catch {
      toast.error(t("toastFailed"))
    } finally {
      setPending(false)
    }
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      disabled={pending}
      className="hidden rounded-none md:inline-flex"
      onClick={handleClick}
    >
      <LifeBuoyIcon data-icon="inline-start" />
      {t("label")}
    </Button>
  )
}
