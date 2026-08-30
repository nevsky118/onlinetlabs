"use client"

import { Button } from "@repo/design-system/ui/button"
import { Spinner } from "@repo/design-system/ui/spinner"
import { LogOut, ShieldCheck } from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { useAccountSessions } from "../hooks/use-account-sessions"
import { SettingsRow } from "./settings-section"

export function SecurityControl() {
  const t = useTranslations("dashboard.settings.security")
  const { activeCount, signOutEverywhere, signOut, isBusy } =
    useAccountSessions(() => toast.error(t("toastSignOutFailed")))

  return (
    <div className="flex flex-col">
      <SettingsRow label={t("activeSessions")} hint={t("activeSessionsHint")}>
        <span className="font-mono text-sm tabular-nums">
          {activeCount ?? "—"}
        </span>
      </SettingsRow>
      <SettingsRow
        label={t("signOutEverywhere")}
        hint={t("signOutEverywhereHint")}
      >
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={isBusy}
          onClick={() => signOutEverywhere()}
        >
          {isBusy ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <ShieldCheck data-icon="inline-start" />
          )}
          {t("signOutEverywhereButton")}
        </Button>
      </SettingsRow>
      <SettingsRow label={t("currentSession")} hint={t("currentSessionHint")}>
        <Button
          type="button"
          size="sm"
          disabled={isBusy}
          onClick={() => signOut()}
        >
          <LogOut data-icon="inline-start" />
          {t("signOutButton")}
        </Button>
      </SettingsRow>
    </div>
  )
}
