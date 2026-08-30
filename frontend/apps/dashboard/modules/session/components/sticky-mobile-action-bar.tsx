"use client"

import { Button } from "@repo/design-system/ui/button"
import { ExternalLinkIcon, SquareIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useTransition } from "react"
import { toast } from "sonner"
import type { Credentials, SessionStatus } from "../types"

export function StickyMobileActionBar({
  status,
  credentials,
  onStopAll,
}: {
  status: SessionStatus
  credentials: Credentials
  onStopAll: () => Promise<void>
}) {
  const t = useTranslations("dashboard.session.stickyMobileActionBar")
  const [pending, startTransition] = useTransition()
  if (status === "ended") return null

  const stop = () =>
    startTransition(async () => {
      try {
        await onStopAll()
        toast.success(t("toastStopped"))
      } catch (error) {
        toast.error((error as Error).message)
      }
    })

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 flex gap-2 border-t bg-background px-4 py-3 md:hidden">
      <Button
        nativeButton={false}
        className="flex-1 rounded-none"
        render={
          // oxlint-disable-next-line jsx-a11y/anchor-has-content -- link text comes from the Base UI render slot
          <a href={credentials.gns3DeepUrl} target="_blank" rel="noreferrer" />
        }
      >
        {t("openGns3")}
        <ExternalLinkIcon data-icon="inline-end" />
      </Button>
      <Button
        variant="outline"
        className="rounded-none text-destructive hover:text-destructive"
        disabled={pending}
        onClick={stop}
        aria-label={t("stopAriaLabel")}
      >
        <SquareIcon data-icon="inline-start" />
        {t("stop")}
      </Button>
    </div>
  )
}
