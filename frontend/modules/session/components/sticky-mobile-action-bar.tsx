"use client"

import { ExternalLinkIcon, SquareIcon } from "lucide-react"
import { useTransition } from "react"
import { toast } from "sonner"
import type { Credentials, SessionStatus } from "../types"
import { Button } from "@/ui/button"

export function StickyMobileActionBar({
  status,
  credentials,
  onStopAll,
}: {
  status: SessionStatus
  credentials: Credentials
  onStopAll: () => Promise<void>
}) {
  const [pending, startTransition] = useTransition()
  if (status === "ended") return null

  const stop = () =>
    startTransition(async () => {
      try {
        await onStopAll()
        toast.success("Узлы остановлены")
      } catch (e) {
        toast.error((e as Error).message)
      }
    })

  return (
    <div className="bg-background fixed inset-x-0 bottom-0 z-40 flex gap-2 border-t px-4 py-3 md:hidden">
      <Button asChild className="flex-1 rounded-none">
        <a href={credentials.gns3DeepUrl} target="_blank" rel="noreferrer">
          Открыть GNS3
          <ExternalLinkIcon data-icon="inline-end" />
        </a>
      </Button>
      <Button
        variant="outline"
        className="rounded-none text-destructive hover:text-destructive"
        disabled={pending}
        onClick={stop}
        aria-label="Остановить узлы"
      >
        <SquareIcon data-icon="inline-start" />
        Стоп
      </Button>
    </div>
  )
}
