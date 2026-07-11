"use client"

import { ExternalLinkIcon, RotateCwIcon, SquareIcon } from "lucide-react"
import { useTransition } from "react"
import { toast } from "sonner"
import type { Credentials, FullSessionState } from "../types"
import { TopologyPreview } from "./topology-preview"
import { Button } from "@/ui/button"

function formatUptime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m < 60) return `${m} мин ${s} с`
  const h = Math.floor(m / 60)
  return `${h} ч ${m % 60} м`
}

export function SessionHero({
  state,
  credentials,
  disabled,
  onStopAll,
  onRestartAll,
}: {
  state: FullSessionState
  credentials: Credentials
  disabled: boolean
  onStopAll: () => Promise<void>
  onRestartAll: () => Promise<void>
}) {
  const [pending, startTransition] = useTransition()
  const run = (fn: () => Promise<void>, ok: string) =>
    startTransition(async () => {
      try {
        await fn()
        toast.success(ok)
      } catch (e) {
        toast.error((e as Error).message)
      }
    })

  return (
    <div className="bg-card border">
      {/* Desktop control bar — hidden on mobile because StickyMobileActionBar
          covers Stop/Open GNS3 and per-action mobile UX is uncluttered. */}
      <div className="hidden items-center justify-between border-b px-4 py-3 md:flex">
        <span className="text-muted-foreground text-xs tracking-wide uppercase">
          Текущая сессия
        </span>
        <div className="flex gap-2">
          <Button
            nativeButton={false}
            variant="outline"
            size="sm"
            className="rounded-none"
            render={
              // biome-ignore lint/a11y/useAnchorContent: контент приходит из render-слота Base UI
              <a
                href={credentials.gns3DeepUrl}
                target="_blank"
                rel="noreferrer"
              />
            }
          >
            Открыть GNS3
            <ExternalLinkIcon data-icon="inline-end" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="rounded-none"
            disabled={disabled || pending}
            onClick={() => run(onStopAll, "Узлы остановлены")}
          >
            <SquareIcon data-icon="inline-start" />
            Остановить
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="rounded-none"
            disabled={disabled || pending}
            onClick={() => run(onRestartAll, "Узлы перезапущены")}
          >
            <RotateCwIcon data-icon="inline-start" />
            Перезапустить
          </Button>
        </div>
      </div>
      {/* Mobile: single "Перезапустить" button — Open GNS3 + Stop are in StickyMobileActionBar. */}
      <div className="flex items-center justify-between gap-3 border-b px-4 py-3 md:hidden">
        <span className="text-muted-foreground truncate text-xs tracking-wide uppercase">
          Текущая сессия
        </span>
        <Button
          variant="outline"
          size="sm"
          className="shrink-0 rounded-none"
          disabled={disabled || pending}
          onClick={() => run(onRestartAll, "Узлы перезапущены")}
        >
          <RotateCwIcon data-icon="inline-start" />
          Перезапустить
        </Button>
      </div>
      <div className="grid divide-x md:grid-cols-[240px_1fr]">
        <div className="flex items-center justify-center p-4">
          <TopologyPreview nodes={state.nodes} links={state.links} />
        </div>
        <div className="grid grid-cols-2 gap-3 p-4 text-sm">
          <Field label="Лаба" value={state.lab.title ?? state.lab.slug} />
          <Field
            label="Доступ к GNS3"
            value={
              <code className="font-mono text-xs">{credentials.gns3Url}</code>
            }
          />
          <Field
            label="Узлов запущено"
            value={`${state.metrics.nodesStarted} / ${state.metrics.nodesTotal}`}
          />
          <Field label="Links" value={state.metrics.linksCount} />
          <Field
            label="Время в работе"
            value={formatUptime(state.metrics.uptimeSeconds)}
          />
        </div>
      </div>
    </div>
  )
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-muted-foreground text-xs tracking-wide uppercase">
        {label}
      </div>
      <div className="mt-0.5">{value}</div>
    </div>
  )
}
