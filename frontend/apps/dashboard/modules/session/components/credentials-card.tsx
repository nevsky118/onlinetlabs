"use client"

import { track } from "@repo/api/analytics"
import { Button } from "@repo/design-system/ui/button"
import { CopyIcon, ExternalLinkIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import type { Credentials } from "../types"

type CredentialField = "username" | "url"

const ANALYTICS_FIELD: Record<CredentialField, string> = {
  username: "username",
  url: "gns3_url",
}

export function CredentialsCard({ credentials }: { credentials: Credentials }) {
  const t = useTranslations("dashboard.session.credentialsCard")

  async function copyField(value: string, field: CredentialField) {
    await navigator.clipboard.writeText(value)
    track("credential_copied", { field: ANALYTICS_FIELD[field] })
    toast.success(t("copiedToast", { label: t(`fields.${field}`) }))
  }

  return (
    <div className="border bg-card p-4">
      <div className="mb-3 text-xs tracking-wide text-muted-foreground uppercase">
        {t("heading")}
      </div>
      <div className="flex flex-col gap-2 text-sm">
        <CredentialRow label={t("fields.username")}>
          <code className="font-mono text-xs">{credentials.gns3Username}</code>
          <CopyButton
            onClick={() => copyField(credentials.gns3Username, "username")}
            ariaLabel={t("copyUsername")}
          />
        </CredentialRow>
        <CredentialRow label="URL">
          <code className="font-mono text-xs">{credentials.gns3Url}</code>
        </CredentialRow>
      </div>
      <Button
        nativeButton={false}
        variant="outline"
        size="sm"
        className="mt-3 w-full rounded-none"
        render={
          // oxlint-disable-next-line jsx-a11y/anchor-has-content -- link text comes from the Base UI render slot
          <a href={credentials.gns3DeepUrl} target="_blank" rel="noreferrer" />
        }
      >
        {t("openGns3")}
        <ExternalLinkIcon data-icon="inline-end" />
      </Button>
    </div>
  )
}

function CredentialRow({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-2 border-b pb-2 last:border-b-0">
      <span className="text-muted-foreground">{label}</span>
      <div className="flex items-center gap-1">{children}</div>
    </div>
  )
}

function CopyButton({
  onClick,
  ariaLabel,
}: {
  onClick: () => void
  ariaLabel: string
}) {
  return (
    <Button
      variant="ghost"
      size="icon-sm"
      className="size-6 rounded-none"
      onClick={onClick}
      aria-label={ariaLabel}
    >
      <CopyIcon />
    </Button>
  )
}
