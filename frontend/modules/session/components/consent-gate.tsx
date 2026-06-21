"use client"

import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/ui/button"

interface ConsentGateProps {
  onConsented?: () => void
}

export function ConsentGate({ onConsented }: ConsentGateProps) {
  const [pending, setPending] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  if (dismissed) return null

  async function handleAccept() {
    setPending(true)
    try {
      const r = await fetch("/api/users/consent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scope: "study", observe: true, act: true }),
      })
      if (!r.ok) throw new Error(`${r.status}`)
      setDismissed(true)
      toast.success("Согласие получено")
      onConsented?.()
    } catch {
      toast.error("Не удалось сохранить согласие")
    } finally {
      setPending(false)
    }
  }

  function handleDecline() {
    setDismissed(true)
  }

  return (
    <div className="border border-foreground bg-background p-4">
      <p className="text-sm font-medium">Участие в исследовании</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Платформа собирает данные о действиях в лабораторной среде для адаптации
        обучения. Данные обезличены и используются только для исследовательских
        целей.
      </p>
      <div className="mt-3 flex gap-2">
        <Button
          type="button"
          size="sm"
          disabled={pending}
          className="rounded-none"
          onClick={handleAccept}
        >
          {pending ? "…" : "Принять"}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={pending}
          className="rounded-none"
          onClick={handleDecline}
        >
          Отклонить
        </Button>
      </div>
    </div>
  )
}
