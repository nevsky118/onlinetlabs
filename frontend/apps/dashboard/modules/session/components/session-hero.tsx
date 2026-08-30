"use client"

import { formatDurationFine } from "@/lib/format-duration"
import { Button } from "@repo/design-system/ui/button"
import { ExternalLinkIcon, RotateCwIcon, SquareIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useTransition } from "react"
import { toast } from "sonner"
import type { Credentials, FullSessionState } from "../types"
import { TopologyPreview } from "./topology-preview"

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
  const t = useTranslations("dashboard.session.sessionHero")
  const durationT = useTranslations("dashboard.session.duration")
  const [pending, startTransition] = useTransition()
  const run = (fn: () => Promise<void>, ok: string) =>
    startTransition(async () => {
      try {
        await fn()
        toast.success(ok)
      } catch (error) {
        toast.error((error as Error).message)
      }
    })

  return (
    <div className="border bg-card">
      {/* Desktop control bar — hidden on mobile because StickyMobileActionBar
          covers Stop/Open GNS3 and per-action mobile UX is uncluttered. */}
      <div className="hidden items-center justify-between border-b px-4 py-3 md:flex">
        <span className="text-xs tracking-wide text-muted-foreground uppercase">
          {t("currentSession")}
        </span>
        <div className="flex gap-2">
          <Button
            nativeButton={false}
            variant="outline"
            size="sm"
            className="rounded-none"
            render={
              // oxlint-disable-next-line jsx-a11y/anchor-has-content -- link text comes from the Base UI render slot
              <a
                href={credentials.gns3DeepUrl}
                target="_blank"
                rel="noreferrer"
              />
            }
          >
            {t("openGns3")}
            <ExternalLinkIcon data-icon="inline-end" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="rounded-none"
            disabled={disabled || pending}
            onClick={() => run(onStopAll, t("toastNodesStopped"))}
          >
            <SquareIcon data-icon="inline-start" />
            {t("stop")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="rounded-none"
            disabled={disabled || pending}
            onClick={() => run(onRestartAll, t("toastNodesRestarted"))}
          >
            <RotateCwIcon data-icon="inline-start" />
            {t("restart")}
          </Button>
        </div>
      </div>
      {/* Mobile: single "Restart" button. Open GNS3 + Stop are in StickyMobileActionBar. */}
      <div className="flex items-center justify-between gap-3 border-b px-4 py-3 md:hidden">
        <span className="truncate text-xs tracking-wide text-muted-foreground uppercase">
          {t("currentSession")}
        </span>
        <Button
          variant="outline"
          size="sm"
          className="shrink-0 rounded-none"
          disabled={disabled || pending}
          onClick={() => run(onRestartAll, t("toastNodesRestarted"))}
        >
          <RotateCwIcon data-icon="inline-start" />
          {t("restart")}
        </Button>
      </div>
      <div className="grid divide-x md:grid-cols-[240px_1fr]">
        <div className="flex items-center justify-center p-4">
          <TopologyPreview nodes={state.nodes} links={state.links} />
        </div>
        <div className="grid grid-cols-2 gap-3 p-4 text-sm">
          <Field label={t("lab")} value={state.lab.title ?? state.lab.slug} />
          <Field
            label={t("gns3Access")}
            value={
              <code className="font-mono text-xs">{credentials.gns3Url}</code>
            }
          />
          <Field
            label={t("nodesStarted")}
            value={`${state.metrics.nodesStarted} / ${state.metrics.nodesTotal}`}
          />
          <Field label="Links" value={state.metrics.linksCount} />
          <Field
            label={t("uptime")}
            value={formatDurationFine(state.metrics.uptimeSeconds, durationT)}
          />
        </div>
      </div>
    </div>
  )
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs tracking-wide text-muted-foreground uppercase">
        {label}
      </div>
      <div className="mt-0.5">{value}</div>
    </div>
  )
}
