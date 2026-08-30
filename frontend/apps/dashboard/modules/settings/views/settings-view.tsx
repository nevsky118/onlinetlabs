"use client"

import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@repo/design-system/ui/avatar"
import { Badge } from "@repo/design-system/ui/badge"
import { useTranslations } from "next-intl"
import type { SettingsAccount } from "../types"
import { ConsentControl } from "../components/consent-control"
import { ModelControl } from "../components/model-control"
import { SecurityControl } from "../components/security-control"
import { SettingsRow, SettingsSection } from "../components/settings-section"
import { ThemeControl } from "../components/theme-control"

const KNOWN_ROLES = new Set(["student", "instructor", "admin"])

function roleLabel(role: string, t: (key: string) => string): string {
  return KNOWN_ROLES.has(role) ? t(`roleLabels.${role}`) : role
}

function initials(name?: string | null): string {
  if (!name) return "?"
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

export function SettingsView({ account }: { account: SettingsAccount }) {
  const t = useTranslations("dashboard.settings")
  const role = account.role ?? "student"

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-10 px-4 py-8">
      <SettingsSection title={t("account")}>
        <div className="flex items-center gap-4 py-2">
          <Avatar className="size-12">
            <AvatarImage
              src={account.image ?? undefined}
              alt={account.name ?? ""}
            />
            <AvatarFallback>{initials(account.name)}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <p className="truncate font-semibold">
              {account.name ?? t("noName")}
            </p>
            <p className="truncate text-sm text-muted-foreground">
              {account.email ?? "—"}
            </p>
          </div>
          <Badge className="ml-auto shrink-0">{roleLabel(role, t)}</Badge>
        </div>
      </SettingsSection>

      <SettingsSection title={t("appearance")}>
        <SettingsRow label={t("theme")} hint={t("themeHint")}>
          <ThemeControl />
        </SettingsRow>
      </SettingsSection>

      <SettingsSection title={t("research")}>
        <SettingsRow label={t("consent.label")} hint={t("consent.hint")}>
          <ConsentControl />
        </SettingsRow>
      </SettingsSection>

      <SettingsSection title={t("aiModel")}>
        <SettingsRow label={t("model.label")} hint={t("model.hint")}>
          <ModelControl />
        </SettingsRow>
      </SettingsSection>

      <SettingsSection title={t("security.title")}>
        <SecurityControl />
      </SettingsSection>
    </div>
  )
}
