"use client"

import { track } from "@repo/api/analytics"
import { Button } from "@repo/design-system/ui/button"
import { CopyIcon, ExternalLinkIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import type { Credentials } from "../types"

type Field = "username" | "url"

const FIELD_TRACK: Record<Field, string> = {
  username: "username",
  url: "gns3_url",
}

export function CredentialsCard({ credentials }: { credentials: Credentials }) {
  const t = useTranslations("dashboard.session.credentialsCard")
  const creds = credentials

  async function copy(value: string, field: Field) {
    await navigator.clipboard.writeText(value)
    track("credential_copied", { field: FIELD_TRACK[field] })
    toast.success(t("copiedToast", { label: t(`fields.${field}`) }))
  }

  return (
    <div className="bg-card border p-4">
      <div className="text-muted-foreground mb-3 text-xs tracking-wide uppercase">
        {t("heading")}
      </div>
      <div className="space-y-2 text-sm">
        <Row label={t("fields.username")}>
          <code className="font-mono text-xs">{creds.gns3Username}</code>
          <IconBtn
            onClick={() => copy(creds.gns3Username, "username")}
            ariaLabel={t("copyUsername")}
          >
            <CopyIcon />
          </IconBtn>
        </Row>
        <Row label="URL">
          <code className="font-mono text-xs">{creds.gns3Url}</code>
        </Row>
      </div>
      <Button
        nativeButton={false}
        variant="outline"
        size="sm"
        className="mt-3 w-full rounded-none"
        render={
          // biome-ignore lint/a11y/useAnchorContent: content comes from the Base UI render slot
          <a href={creds.gns3DeepUrl} target="_blank" rel="noreferrer" />
        }
      >
        {t("openGns3")}
        <ExternalLinkIcon data-icon="inline-end" />
      </Button>
    </div>
  )
}

function Row({
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

function IconBtn({
  onClick,
  ariaLabel,
  children,
}: {
  onClick: () => void
  ariaLabel: string
  children: React.ReactNode
}) {
  return (
    <Button
      variant="ghost"
      size="icon-sm"
      className="size-6 rounded-none"
      onClick={onClick}
      aria-label={ariaLabel}
    >
      {children}
    </Button>
  )
}
