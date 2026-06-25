"use client"

import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import type { AdminLab } from "../types"
import { rebuildLabTemplate, updateAdminLab } from "../actions"
import { cn } from "@/shared/lib/utils"
import { Alert, AlertDescription, AlertTitle } from "@/ui/alert"
import { Badge } from "@/ui/badge"
import { Button } from "@/ui/button"
import { Skeleton } from "@/ui/skeleton"
import { Spinner } from "@/ui/spinner"
import { Switch } from "@/ui/switch"

interface LabsViewProps {
  data: AdminLab[] | null
  error: string | null
}

function StatusBadge({ status, ready }: { status: string; ready: boolean }) {
  if (status === "building") {
    return (
      <Badge variant="outline">
        <Spinner data-icon="inline-start" />
        Сборка
      </Badge>
    )
  }
  if (status === "ready") {
    return <Badge>Готов</Badge>
  }
  if (status === "error") {
    return <Badge variant="outline">Ошибка</Badge>
  }
  if (ready) {
    return <Badge variant="secondary">Готов</Badge>
  }
  return <Badge variant="outline">Нет</Badge>
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
        <div className="font-medium text-sm">{lab.title}</div>
        <div className="text-muted-foreground text-xs tabular-nums">
          {lab.slug}
        </div>
      </td>
      <td className="py-3 pr-4 text-sm">{lab.environmentType}</td>
      <td className="py-3 pr-4">
        <StatusBadge status={lab.templateStatus} ready={lab.templateReady} />
      </td>
      <td className="py-3 pr-4">
        {lab.gns3TemplateProjectId ? (
          <span
            className="max-w-[160px] truncate block text-sm tabular-nums"
            title={lab.gns3TemplateProjectId}
          >
            {lab.gns3TemplateProjectId}
          </span>
        ) : (
          <span className="text-muted-foreground text-sm">—</span>
        )}
      </td>
      <td className="py-3 pr-4">
        <Switch
          size="sm"
          checked={lab.enabled}
          onCheckedChange={handleToggle}
          disabled={toggling}
          aria-label="Включить лабу"
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
                Сборка…
              </>
            ) : (
              "Пересобрать"
            )}
          </Button>
        )}
      </td>
    </tr>
  )
}

export function LabsView({ data, error }: LabsViewProps) {
  const router = useRouter()
  const [labs, setLabs] = useState<AdminLab[]>(data ?? [])

  useEffect(() => {
    setLabs(data ?? [])
  }, [data])

  // polling — refresh every 5s while any lab is building
  useEffect(() => {
    const anyBuilding = labs.some((l) => l.templateStatus === "building")
    if (!anyBuilding) return
    const id = setInterval(() => router.refresh(), 5000)
    return () => clearInterval(id)
  }, [labs, router])

  const handleToggle = async (slug: string, enabled: boolean) => {
    const result = await updateAdminLab(slug, { enabled })
    if (result.ok) {
      setLabs((prev) => prev.map((l) => (l.slug === slug ? result.lab : l)))
      toast.success(enabled ? "Лаба включена" : "Лаба отключена")
      router.refresh()
    } else {
      toast.error(result.error)
    }
  }

  const handleRebuild = async (slug: string) => {
    // optimistic
    setLabs((prev) =>
      prev.map((l) =>
        l.slug === slug ? { ...l, templateStatus: "building" } : l
      )
    )
    const result = await rebuildLabTemplate(slug)
    if (result.ok) {
      toast.success("Сборка запущена")
    } else {
      toast.error(result.error)
      // revert
      setLabs((prev) =>
        prev.map((l) =>
          l.slug === slug ? { ...l, templateStatus: "unknown" } : l
        )
      )
    }
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Ошибка</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!data && !error) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 5 }, (_, i) => (
          <Skeleton key={`skel-${i}`} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (labs.length === 0) {
    return (
      <p className="py-8 text-center text-muted-foreground text-sm">Лаб нет</p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="py-2 pr-4 text-left font-medium">Лаба</th>
            <th className="py-2 pr-4 text-left font-medium">Среда</th>
            <th className="py-2 pr-4 text-left font-medium">Статус шаблона</th>
            <th className="py-2 pr-4 text-left font-medium">Шаблон ID</th>
            <th className="py-2 pr-4 text-left font-medium">Включена</th>
            <th className="py-2 text-left font-medium">Действия</th>
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
