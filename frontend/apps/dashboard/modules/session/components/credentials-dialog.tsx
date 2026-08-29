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
  result,
  open,
  onOpenChange,
}: {
  result: SessionData | null
  open: boolean
  onOpenChange: (v: boolean) => void
}) {
  const t = useTranslations("dashboard.session.credentialsDialog")
  const router = useRouter()
  if (!result) return null

  async function copy(value: string, field: "username" | "password") {
    await navigator.clipboard.writeText(value)
    toast.success(t("copiedToast", { label: t(`fields.${field}`) }))
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
            <span className="text-muted-foreground text-sm">
              {t("fields.username")}:
            </span>
            <code className="text-sm">{result.gns3Username}</code>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => copy(result.gns3Username, "username")}
            >
              <CopyIcon />
            </Button>
          </div>
          <Button
            nativeButton={false}
            variant="outline"
            className="w-fit rounded-none"
            render={
              // biome-ignore lint/a11y/useAnchorContent: content comes from the Base UI render slot
              <a href={result.gns3DeepUrl} target="_blank" rel="noreferrer" />
            }
          >
            {t("openGns3")} <ExternalLinkIcon data-icon="inline-end" />
          </Button>
        </div>
        <DialogFooter>
          <Button onClick={() => router.push(`/session/${result.sessionId}`)}>
            {t("goToLab")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
