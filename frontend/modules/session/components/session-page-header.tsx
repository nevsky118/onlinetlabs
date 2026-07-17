import { BanIcon, ChevronLeftIcon } from "lucide-react"
import Link from "next/link"
import type { SessionStatus } from "../types"
import { Badge } from "@/ui/badge"

const STATUS_LABEL: Record<SessionStatus, string> = {
  provisioning: "Создаётся",
  active: "Активна",
  ended: "Завершена",
  error: "Ошибка",
}

const STATUS_VARIANT: Record<
  SessionStatus,
  "default" | "secondary" | "outline" | "destructive"
> = {
  provisioning: "secondary",
  active: "default",
  ended: "outline",
  error: "destructive",
}

export function SessionPageHeader({
  lab,
  status,
  noAssist,
}: {
  lab: { slug: string; title: string | null }
  status: SessionStatus
  noAssist: boolean
}) {
  return (
    <div className="flex min-w-0 items-center gap-2 text-sm">
      {/* Back to labs: icon-only on mobile, icon+label on desktop. */}
      <Link
        href="/labs"
        className="text-muted-foreground hover:text-foreground inline-flex shrink-0 items-center gap-1"
        aria-label="Назад к лабам"
      >
        <ChevronLeftIcon className="size-4" />
        <span className="hidden sm:inline">Лабы</span>
      </Link>
      <span className="text-muted-foreground hidden sm:inline">/</span>
      {/* Title: truncate to one line, keep status badge inline. */}
      <Link
        href={`/labs/${lab.slug}`}
        className="min-w-0 truncate font-medium hover:underline"
      >
        {lab.title ?? lab.slug}
      </Link>
      <Badge variant={STATUS_VARIANT[status]} className="shrink-0 rounded-none">
        {status === "active" && (
          <span className="mr-1.5 inline-block size-2 rounded-full bg-emerald-500" />
        )}
        {STATUS_LABEL[status]}
      </Badge>
      {noAssist && (
        <Badge
          variant="default"
          className="shrink-0 uppercase tracking-wide"
          title="Проактивные подсказки отключены в этой сессии (near-transfer)"
        >
          <BanIcon data-icon="inline-start" />
          Без подсказок
        </Badge>
      )}
    </div>
  )
}
