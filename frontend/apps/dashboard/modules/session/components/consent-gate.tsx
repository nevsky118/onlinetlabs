"use client"

import { Button } from "@repo/design-system/ui/button"
import { Link } from "@repo/i18n/navigation"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { toast } from "sonner"

// Local record of the decision (accepted/declined), so the banner does not show
// up again on every hard refresh. The server is the source of truth for "accepted".
const DISMISS_KEY = "study_consent_dismissed"

interface ConsentGateProps {
  onConsented?: () => void
}

export function ConsentGate({ onConsented }: ConsentGateProps) {
  const t = useTranslations("dashboard.session.consentGate")
  const [show, setShow] = useState(false)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function check() {
      // Already decided locally, do not show it.
      if (localStorage.getItem(DISMISS_KEY)) return
      try {
        const r = await fetch("/api/users/consent", { cache: "no-store" })
        if (!r.ok) return
        const items: { scope: string }[] = await r.json()
        const granted = items.some((c) => c.scope === "study")
        if (granted) localStorage.setItem(DISMISS_KEY, "1")
        if (!cancelled && !granted) setShow(true)
      } catch {
        // Network error, do not block the session with a banner.
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
      toast.success(t("toastAccepted"))
      onConsented?.()
    } catch {
      toast.error(t("toastFailed"))
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
      <p className="text-sm font-medium">{t("title")}</p>
      <p className="mt-1 text-sm text-muted-foreground">
        {t.rich("description", {
          settingsLink: (chunks) => (
            <Link href="/settings" className="underline underline-offset-2">
              {chunks}
            </Link>
          ),
        })}
      </p>
      <div className="mt-3 flex gap-2">
        <Button
          type="button"
          size="sm"
          disabled={pending}
          onClick={handleAccept}
        >
          {pending ? "…" : t("accept")}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={pending}
          onClick={handleDecline}
        >
          {t("decline")}
        </Button>
      </div>
    </div>
  )
}
