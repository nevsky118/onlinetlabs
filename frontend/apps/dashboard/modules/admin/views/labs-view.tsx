"use client"

import { cn } from "@repo/design-system/lib/utils"
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@repo/design-system/ui/alert"
import { Badge } from "@repo/design-system/ui/badge"
import { Button } from "@repo/design-system/ui/button"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { Spinner } from "@repo/design-system/ui/spinner"
import { Switch } from "@repo/design-system/ui/switch"
import { useTranslations } from "next-intl"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import type { AdminLab } from "../types"
import { rebuildLabTemplate, updateAdminLab } from "../actions"

interface LabsViewProps {
  data: AdminLab[] | null
  error: string | null
}

function StatusBadge({
  status,
  ready,
  t,
}: {
  status: string
  ready: boolean
  t: (key: string) => string
}) {
  if (status === "building") {
    return (
      <Badge variant="outline">
        <Spinner data-icon="inline-start" />
        {t("statusBuilding")}
      </Badge>
    )
  }
  if (status === "ready") {
    return <Badge>{t("statusReady")}</Badge>
  }
  if (status === "error") {
    return <Badge variant="outline">{t("statusError")}</Badge>
  }
  if (ready) {
    return <Badge variant="secondary">{t("statusReady")}</Badge>
  }
  return <Badge variant="outline">{t("statusNone")}</Badge>
}

function LabRow({
  lab,
  onToggle,
  onRebuild,
}: {
  lab: AdminLab
  onToggle: (slug: string, enabled: boolean) => Promise<void>
  onRebuild: (slug: string) => Promise<void>
}) {
  const t = useTranslations("dashboard.admin.labs")
  const [toggling, setToggling] = useState(false)
  const building = lab.templateStatus === "building"

  const handleToggle = async (checked: boolean) => {
    setToggling(true)
    try {
      await onToggle(lab.slug, checked)
    } finally {
      setToggling(false)
    }
  }

  return (
    <tr className={cn("border-b border-border", toggling && "opacity-60")}>
      <td className="py-3 pr-4">
        <div className="text-sm font-medium">{lab.title}</div>
        <div className="text-xs text-muted-foreground tabular-nums">
          {lab.slug}
        </div>
      </td>
      <td className="py-3 pr-4 text-sm">{lab.environmentType}</td>
      <td className="py-3 pr-4">
        <StatusBadge
          status={lab.templateStatus}
          ready={lab.templateReady}
          t={t}
        />
      </td>
      <td className="py-3 pr-4">
        {lab.gns3TemplateProjectId ? (
          <span
            className="block max-w-[160px] truncate text-sm tabular-nums"
            title={lab.gns3TemplateProjectId}
          >
            {lab.gns3TemplateProjectId}
          </span>
        ) : (
          <span className="text-sm text-muted-foreground">—</span>
        )}
      </td>
      <td className="py-3 pr-4">
        <Switch
          size="sm"
          checked={lab.enabled}
          onCheckedChange={handleToggle}
          disabled={toggling}
          aria-label={t("toggleAriaLabel")}
        />
      </td>
      <td className="py-3">
        {lab.environmentType === "gns3" && (
          <Button
            variant="outline"
            size="sm"
            type="button"
            disabled={building}
            onClick={() => onRebuild(lab.slug)}
          >
            {building ? (
              <>
                <Spinner data-icon="inline-start" />
                {t("rebuilding")}
              </>
            ) : (
              t("rebuildButton")
            )}
          </Button>
        )}
      </td>
    </tr>
  )
}

export function LabsView({ data, error }: LabsViewProps) {
  const t = useTranslations("dashboard.admin.labs")
  const router = useRouter()
  const [labs, setLabs] = useState<AdminLab[]>(data ?? [])
  // Adjust during render rather than in an effect: a fresh server payload
  // replaces the optimistic copy without an extra commit.
  const [syncedData, setSyncedData] = useState(data)
  if (data !== syncedData) {
    setSyncedData(data)
    setLabs(data ?? [])
  }

  // polling — refresh every 5s while any lab is building
  useEffect(() => {
    const anyBuilding = labs.some((lab) => lab.templateStatus === "building")
    if (!anyBuilding) return
    const id = setInterval(() => router.refresh(), 5000)
    return () => clearInterval(id)
  }, [labs, router])

  const handleToggle = async (slug: string, enabled: boolean) => {
    const result = await updateAdminLab(slug, { enabled })
    if (result.ok) {
      setLabs((prev) =>
        prev.map((lab) => (lab.slug === slug ? result.lab : lab))
      )
      toast.success(enabled ? t("toastEnabled") : t("toastDisabled"))
      router.refresh()
    } else {
      toast.error(result.error)
    }
  }

  const handleRebuild = async (slug: string) => {
    // optimistic
    setLabs((prev) =>
      prev.map((lab) =>
        lab.slug === slug ? { ...lab, templateStatus: "building" } : lab
      )
    )
    const result = await rebuildLabTemplate(slug)
    if (result.ok) {
      toast.success(t("toastRebuildStarted"))
    } else {
      toast.error(result.error)
      // revert
      setLabs((prev) =>
        prev.map((lab) =>
          lab.slug === slug ? { ...lab, templateStatus: "unknown" } : lab
        )
      )
    }
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>{t("errorTitle")}</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!data && !error) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 5 }, (_, index) => (
          <Skeleton key={`skel-${index}`} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (labs.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        {t("empty")}
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="py-2 pr-4 text-left font-medium">
              {t("headers.lab")}
            </th>
            <th className="py-2 pr-4 text-left font-medium">
              {t("headers.environment")}
            </th>
            <th className="py-2 pr-4 text-left font-medium">
              {t("headers.templateStatus")}
            </th>
            <th className="py-2 pr-4 text-left font-medium">
              {t("headers.templateId")}
            </th>
            <th className="py-2 pr-4 text-left font-medium">
              {t("headers.enabled")}
            </th>
            <th className="py-2 text-left font-medium">
              {t("headers.actions")}
            </th>
          </tr>
        </thead>
        <tbody>
          {labs.map((lab) => (
            <LabRow
              key={lab.slug}
              lab={lab}
              onToggle={handleToggle}
              onRebuild={handleRebuild}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
