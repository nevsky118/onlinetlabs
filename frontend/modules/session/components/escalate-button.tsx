"use client"

import { LifeBuoyIcon } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/ui/button"

export function EscalateButton({ sessionId }: { sessionId: string }) {
  const [pending, setPending] = useState(false)

  async function handleClick() {
    setPending(true)
    try {
      const r = await fetch(`/api/sessions/${sessionId}/escalate`, {
        method: "POST",
      })
      if (!r.ok) throw new Error(`${r.status}`)
      toast.success("Запрос наставнику отправлен")
    } catch {
      toast.error("Не удалось отправить запрос наставнику")
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
      Нужен наставник
    </Button>
  )
}
