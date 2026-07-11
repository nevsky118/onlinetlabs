"use client"

import { CopyIcon, ExternalLinkIcon, EyeIcon, EyeOffIcon } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import type { Credentials } from "../types"
import { fetchCredentials } from "../actions"
import { track } from "@/lib/analytics"
import { Button } from "@/ui/button"

export function CredentialsCard({
  sessionId,
  credentials,
}: {
  sessionId: string
  credentials: Credentials
}) {
  const [creds, setCreds] = useState(credentials)
  const [reveal, setReveal] = useState(false)

  async function copy(value: string, label: string) {
    await navigator.clipboard.writeText(value)
    const fieldMap: Record<string, string> = {
      Логин: "username",
      Пароль: "password",
      URL: "gns3_url",
    }
    track("credential_copied", { field: fieldMap[label] ?? label })
    toast.success(`${label} скопирован`)
  }

  async function toggleReveal() {
    if (!reveal) setCreds(await fetchCredentials(sessionId))
    setReveal((v) => !v)
  }

  return (
    <div className="bg-card border p-4">
      <div className="text-muted-foreground mb-3 text-xs tracking-wide uppercase">
        Доступ к GNS3
      </div>
      <div className="space-y-2 text-sm">
        <Row label="Логин">
          <code className="font-mono text-xs">{creds.gns3Username}</code>
          <IconBtn
            onClick={() => copy(creds.gns3Username, "Логин")}
            ariaLabel="Скопировать логин"
          >
            <CopyIcon />
          </IconBtn>
        </Row>
        <Row label="Пароль">
          <code className="font-mono text-xs">
            {reveal ? creds.gns3Password : "••••••••"}
          </code>
          <IconBtn
            onClick={toggleReveal}
            ariaLabel={reveal ? "Скрыть пароль" : "Показать пароль"}
          >
            {reveal ? <EyeOffIcon /> : <EyeIcon />}
          </IconBtn>
          <IconBtn
            onClick={() => copy(creds.gns3Password, "Пароль")}
            ariaLabel="Скопировать пароль"
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
          // biome-ignore lint/a11y/useAnchorContent: контент приходит из render-слота Base UI
          <a href={creds.gns3DeepUrl} target="_blank" rel="noreferrer" />
        }
      >
        Открыть GNS3
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
