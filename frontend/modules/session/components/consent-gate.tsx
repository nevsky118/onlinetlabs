"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Button } from "@/ui/button"

// Локальная отметка решения (принял/отклонил) — чтобы баннер не появлялся
// повторно при каждом hard refresh. Сервер — источник правды для «принял».
const DISMISS_KEY = "study_consent_dismissed"

interface ConsentGateProps {
  onConsented?: () => void
}

export function ConsentGate({ onConsented }: ConsentGateProps) {
  const [show, setShow] = useState(false)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function check() {
      // Уже решено локально — не показываем.
      if (localStorage.getItem(DISMISS_KEY)) return
      try {
        const r = await fetch("/api/users/consent", { cache: "no-store" })
        if (!r.ok) return
        const items: { scope: string }[] = await r.json()
        const granted = items.some((c) => c.scope === "study")
        if (granted) localStorage.setItem(DISMISS_KEY, "1")
        if (!cancelled && !granted) setShow(true)
      } catch {
        // Сетевая ошибка — не блокируем сессию баннером.
      }
    }
    check()
    return () => {
      cancelled = true
    }
  }, [])

  if (!show) return null

  async function handleAccept() {
    setPending(true)
    try {
      const r = await fetch("/api/users/consent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scope: "study", observe: true, act: true }),
      })
      if (!r.ok) throw new Error(`${r.status}`)
      localStorage.setItem(DISMISS_KEY, "1")
      setShow(false)
      toast.success("Согласие получено")
      onConsented?.()
    } catch {
      toast.error("Не удалось сохранить согласие")
    } finally {
      setPending(false)
    }
  }

  function handleDecline() {
    localStorage.setItem(DISMISS_KEY, "1")
    setShow(false)
  }

  return (
    <div className="border border-foreground bg-background p-4">
      <p className="text-sm font-medium">Участие в исследовании</p>
      <p className="mt-1 text-sm text-muted-foreground">
        Платформа собирает данные о действиях в лабораторной среде для адаптации
        обучения. Данные обезличены и используются только для исследовательских
        целей. Изменить решение можно в{" "}
        <a href="/settings" className="underline underline-offset-2">
          настройках
        </a>
        .
      </p>
      <div className="mt-3 flex gap-2">
        <Button
          type="button"
          size="sm"
          disabled={pending}
          onClick={handleAccept}
        >
          {pending ? "…" : "Принять"}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={pending}
          onClick={handleDecline}
        >
          Отклонить
        </Button>
      </div>
    </div>
  )
}
