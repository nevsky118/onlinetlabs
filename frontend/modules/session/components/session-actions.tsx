"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  BookOpenIcon,
  MoreVerticalIcon,
  RefreshCcwIcon,
  XIcon,
} from "lucide-react"
import Link from "next/link"
import { toast } from "sonner"
import type { SessionStatus } from "../types"
import { endLab, resetLab } from "../actions"
import { sessionKeys } from "../query"
import { track } from "@/lib/analytics"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/ui/alert-dialog"
import { Button } from "@/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/ui/dropdown-menu"

export function SessionActions({
  sessionId,
  status,
  labSlug,
}: {
  sessionId: string
  status: SessionStatus
  labSlug: string
}) {
  const qc = useQueryClient()

  const resetM = useMutation({
    mutationFn: () => resetLab(sessionId),
    onSuccess: () => {
      track("session_reset", { lab_slug: labSlug, session_id: sessionId })
      qc.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })
      toast.success("Лаба сброшена")
    },
    onError: (e) => toast.error((e as Error).message),
  })

  const endM = useMutation({
    mutationFn: () => endLab(sessionId),
    onSuccess: () => {
      track("session_ended", {
        lab_slug: labSlug,
        session_id: sessionId,
        reason: "user",
      })
      qc.invalidateQueries({ queryKey: sessionKeys.state(sessionId) })
      qc.invalidateQueries({ queryKey: sessionKeys.list() })
      toast.success("Сессия завершена")
    },
    onError: (e) => toast.error((e as Error).message),
  })

  const disabled = resetM.isPending || endM.isPending || status === "ended"
  const runReset = () => resetM.mutate()
  const runEnd = () => endM.mutate()

  return (
    <div className="flex shrink-0 items-center gap-2">
      {/* Desktop: full row of buttons. */}
      <Button
        asChild
        variant="outline"
        size="sm"
        className="hidden rounded-none md:inline-flex"
      >
        <Link href={`/labs/${labSlug}`}>
          <BookOpenIcon data-icon="inline-start" />
          Инструкция
        </Link>
      </Button>
      <div className="hidden gap-2 md:flex">
        <ResetButton disabled={disabled} onConfirm={runReset} />
        <EndButton disabled={disabled} onConfirm={runEnd} />
      </div>
      {/* Mobile: all 3 actions consolidated into a kebab menu. */}
      <div className="md:hidden">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className="rounded-none"
              aria-label="Меню действий"
            >
              <MoreVerticalIcon />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuGroup>
              <DropdownMenuItem asChild>
                <Link href={`/labs/${labSlug}`}>
                  <BookOpenIcon /> Инструкция
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem disabled={disabled} onClick={runReset}>
                <RefreshCcwIcon /> Сбросить
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={disabled}
                onClick={runEnd}
                className="text-destructive"
              >
                <XIcon /> Завершить
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}

function ResetButton({
  disabled,
  onConfirm,
}: {
  disabled: boolean
  onConfirm: () => void
}) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled}
          className="rounded-none"
        >
          <RefreshCcwIcon data-icon="inline-start" /> Сбросить
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Сбросить лабораторную?</AlertDialogTitle>
          <AlertDialogDescription>
            Текущая топология в среде потеряется. Проект пересоздаётся из
            шаблона.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Отмена</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}>Сбросить</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

function EndButton({
  disabled,
  onConfirm,
}: {
  disabled: boolean
  onConfirm: () => void
}) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button
          variant="destructive"
          size="sm"
          disabled={disabled}
          className="rounded-none"
        >
          Завершить
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Завершить сессию?</AlertDialogTitle>
          <AlertDialogDescription>
            GNS3-окружение удалится полностью. Действие необратимо.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Отмена</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}>Завершить</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
