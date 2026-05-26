"use client"

import { CopyIcon, ExternalLinkIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import type { SessionData } from "../types"
import { Button } from "@/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/ui/dialog"

export function CredentialsDialog({
  result,
  open,
  onOpenChange,
}: {
  result: SessionData | null
  open: boolean
  onOpenChange: (v: boolean) => void
}) {
  const router = useRouter()
  if (!result) return null

  async function copy(value: string, label: string) {
    await navigator.clipboard.writeText(value)
    toast.success(`${label} скопирован`)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Доступ к лаборатории</DialogTitle>
          <DialogDescription>
            Сохраните пароль — он показывается полностью только сейчас.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground text-sm">Логин:</span>
            <code className="text-sm">{result.gns3Username}</code>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => copy(result.gns3Username, "Логин")}
            >
              <CopyIcon />
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground text-sm">Пароль:</span>
            <code className="text-sm">{result.gns3Password}</code>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => copy(result.gns3Password, "Пароль")}
            >
              <CopyIcon />
            </Button>
          </div>
          <Button asChild variant="outline" className="w-fit rounded-none">
            <a href={result.gns3DeepUrl} target="_blank" rel="noreferrer">
              Открыть GNS3 <ExternalLinkIcon data-icon="inline-end" />
            </a>
          </Button>
        </div>
        <DialogFooter>
          <Button onClick={() => router.push(`/session/${result.sessionId}`)}>
            Перейти к лабе
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
