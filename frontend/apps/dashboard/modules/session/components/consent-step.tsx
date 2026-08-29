"use client"

import {
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@repo/design-system/ui/alert-dialog"
import { Button } from "@repo/design-system/ui/button"
import { Spinner } from "@repo/design-system/ui/spinner"
import { Link } from "@repo/i18n/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

type Decision = "granted" | "declined"

export function ConsentStep({ onAnswered }: { onAnswered: () => void }) {
  const t = useTranslations("dashboard.session.consentGate")
  const [pending, setPending] = useState<Decision | null>(null)

  async function answer(decision: Decision) {
    setPending(decision)
    try {
      const granted = decision === "granted"
      const r = await fetch("/api/users/consent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scope: "study",
          observe: granted,
          act: granted,
          decision,
        }),
      })
      if (!r.ok) throw new Error(`${r.status}`)
      toast.success(granted ? t("toastAccepted") : t("toastDeclined"))
      onAnswered()
    } catch {
      toast.error(t("toastFailed"))
    } finally {
      setPending(null)
    }
  }

  return (
    <>
      <AlertDialogHeader>
        <AlertDialogTitle>{t("title")}</AlertDialogTitle>
        <AlertDialogDescription>
          {t.rich("description", {
            settingsLink: (chunks) => <Link href="/settings">{chunks}</Link>,
          })}
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <Button
          type="button"
          variant="outline"
          disabled={pending !== null}
          onClick={() => answer("declined")}
        >
          {pending === "declined" && <Spinner data-icon="inline-start" />}
          {t("decline")}
        </Button>
        <Button
          type="button"
          disabled={pending !== null}
          onClick={() => answer("granted")}
        >
          {pending === "granted" && <Spinner data-icon="inline-start" />}
          {t("accept")}
        </Button>
      </AlertDialogFooter>
    </>
  )
}
