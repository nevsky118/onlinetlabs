"use client"

import { Button } from "@repo/design-system/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@repo/design-system/ui/dialog"
import { useRouter } from "@repo/i18n/navigation"
import { CopyIcon, ExternalLinkIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import type { SessionData } from "../types"

export function CredentialsDialog({
  session,
  open,
  onOpenChange,
}: {
  session: SessionData | null
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const t = useTranslations("dashboard.session.credentialsDialog")
  const router = useRouter()

  if (!session) return null

  async function copyUsername(username: string) {
    await navigator.clipboard.writeText(username)
    toast.success(t("copiedToast", { label: t("fields.username") }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {t("fields.username")}:
            </span>
            <code className="text-sm">{session.gns3Username}</code>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={t("copyUsername")}
              onClick={() => copyUsername(session.gns3Username)}
            >
              <CopyIcon />
            </Button>
          </div>
          <Button
            nativeButton={false}
            variant="outline"
            className="w-fit rounded-none"
            render={
              // oxlint-disable-next-line jsx-a11y/anchor-has-content -- link text comes from the Base UI render slot
              <a href={session.gns3DeepUrl} target="_blank" rel="noreferrer" />
            }
          >
            {t("openGns3")} <ExternalLinkIcon data-icon="inline-end" />
          </Button>
        </div>
        <DialogFooter>
          <Button onClick={() => router.push(`/session/${session.sessionId}`)}>
            {t("goToLab")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
