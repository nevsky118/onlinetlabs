"use client"

import { useQueuePosition } from "../hooks/use-queue-position"

export function QueueStatus({ labSlug }: { labSlug: string }) {
  const status = useQueuePosition(labSlug)
  if (!status?.inQueue) return null
  const mins = Math.max(1, Math.ceil(status.etaSec / 60))
  return (
    <div className="bg-card text-card-foreground border p-4">
      <div className="text-muted-foreground mb-2 text-xs tracking-wide uppercase">
        В очереди
      </div>
      <div className="text-sm">
        Место{" "}
        <span className="font-medium tabular-nums">{status.position}</span> из{" "}
        <span className="font-medium tabular-nums">{status.depth}</span>
      </div>
      <div className="text-muted-foreground mt-1 text-xs">
        Ожидание ~{mins} мин. Страница обновится автоматически когда подойдёт
        ваша очередь.
      </div>
    </div>
  )
}
