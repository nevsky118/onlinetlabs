"use client"

import { webUrl } from "@/lib/config"
import { useRecordConsentDecision } from "@/modules/consent"
import {
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@repo/design-system/ui/alert-dialog"
import { Button } from "@repo/design-system/ui/button"
import { Spinner } from "@repo/design-system/ui/spinner"
import { Link } from "@repo/i18n/navigation"
import { useLocale, useTranslations } from "next-intl"
import { toast } from "sonner"

export function ConsentStep({ onAnswered }: { onAnswered: () => void }) {
  const t = useTranslations("dashboard.session.consentGate")
  const locale = useLocale()
  const { record, pendingDecision } = useRecordConsentDecision({
    onRecorded: (decision) => {
      toast.success(
        decision === "granted" ? t("toastAccepted") : t("toastDeclined")
      )
      onAnswered()
    },
    onFailed: () => toast.error(t("toastFailed")),
  })

  return (
    <>
      <AlertDialogHeader>
        <AlertDialogTitle>{t("title")}</AlertDialogTitle>
        <AlertDialogDescription>
          {t.rich("description", {
            settingsLink: (chunks) => <Link href="/settings">{chunks}</Link>,
            // The policy lives on the public site, a different origin from the dashboard.
            policyLink: (chunks) => (
              <a
                href={`${webUrl}/${locale}/privacy`}
                target="_blank"
                rel="noreferrer"
                className="underline underline-offset-4"
              >
                {chunks}
              </a>
            ),
          })}
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <Button
          type="button"
          variant="outline"
          disabled={pendingDecision !== null}
          onClick={() => record("declined")}
        >
          {pendingDecision === "declined" && (
            <Spinner data-icon="inline-start" />
          )}
          {t("decline")}
        </Button>
        <Button
          type="button"
          disabled={pendingDecision !== null}
          onClick={() => record("granted")}
        >
          {pendingDecision === "granted" && (
            <Spinner data-icon="inline-start" />
          )}
          {t("accept")}
        </Button>
      </AlertDialogFooter>
    </>
  )
}
