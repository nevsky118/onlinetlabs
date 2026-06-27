"use client"

import { LogOut, ShieldCheck } from "lucide-react"
import { useTheme } from "next-themes"
import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"
import { authClient } from "@/auth/client"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback, AvatarImage } from "@/ui/avatar"
import { Badge } from "@/ui/badge"
import { Button } from "@/ui/button"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/ui/select"
import { Spinner } from "@/ui/spinner"
import { Switch } from "@/ui/switch"

const CONSENT_DISMISS_KEY = "study_consent_dismissed"

interface SettingsAccount {
  name: string | null
  email: string | null
  image: string | null
  role: string | null
}

const ROLE_LABEL: Record<string, string> = {
  student: "Студент",
  instructor: "Инструктор",
  admin: "Администратор",
}

function initials(name?: string | null): string {
  if (!name) return "?"
  return name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

// — Section / Row primitives —

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <h2 className="text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
          {title}
        </h2>
        <span className="h-px flex-1 bg-border" />
      </div>
      {children}
    </section>
  )
}

function Row({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-border border-b py-4 last:border-b-0">
      <div className="min-w-0 max-w-md">
        <p className="text-sm font-medium">{label}</p>
        {hint && <p className="mt-0.5 text-sm text-muted-foreground">{hint}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  )
}

// — Theme —

const THEMES = [
  { value: "light", label: "Светлая" },
  { value: "dark", label: "Тёмная" },
  { value: "system", label: "Системная" },
]

function ThemeControl() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  const current = mounted ? (theme ?? "system") : "system"

  return (
    <div className="inline-flex border border-border">
      {THEMES.map((t, i) => (
        <button
          key={t.value}
          type="button"
          onClick={() => setTheme(t.value)}
          className={cn(
            "px-3 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-inset",
            i > 0 && "border-border border-l",
            current === t.value
              ? "bg-foreground font-medium text-background"
              : "text-muted-foreground hover:bg-foreground/[0.06] hover:text-foreground"
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}

// — Consent —

function ConsentControl() {
  const [granted, setGranted] = useState<boolean | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    fetch("/api/users/consent", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : []))
      .then((items: { scope: string }[]) =>
        setGranted(items.some((c) => c.scope === "study"))
      )
      .catch(() => setGranted(false))
  }, [])

  const toggle = useCallback(async (next: boolean) => {
    setPending(true)
    try {
      const r = next
        ? await fetch("/api/users/consent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ scope: "study", observe: true, act: true }),
          })
        : await fetch("/api/users/consent?scope=study", { method: "DELETE" })
      if (!r.ok) throw new Error(`${r.status}`)
      setGranted(next)
      // Решение принято осознанно — баннер сессии больше не нужен.
      localStorage.setItem(CONSENT_DISMISS_KEY, "1")
      toast.success(next ? "Согласие включено" : "Согласие отозвано")
    } catch {
      toast.error("Не удалось сохранить")
    } finally {
      setPending(false)
    }
  }, [])

  if (granted === null) return <Spinner className="size-4" />

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-muted-foreground tabular-nums">
        {granted ? "Включено" : "Выключено"}
      </span>
      <Switch
        checked={granted}
        disabled={pending}
        onCheckedChange={toggle}
        aria-label="Участие в исследовании"
      />
    </div>
  )
}

// — Default model —

interface ModelOption {
  id: string
  label: string
}

function ModelControl() {
  const [models, setModels] = useState<ModelOption[] | null>(null)
  const [value, setValue] = useState<string>("")
  const [pending, setPending] = useState(false)

  useEffect(() => {
    fetch("/api/chat/models", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!d) return setModels([])
        const raw: Record<string, unknown>[] = Array.isArray(d)
          ? d
          : ((d.models ?? []) as Record<string, unknown>[])
        setModels(
          raw.map((m) => ({
            id: String(m.id),
            label: String(m.label ?? m.name ?? m.id),
          }))
        )
      })
      .catch(() => setModels([]))
    // Сохранённый выбор — с сервера (источник правды), не localStorage.
    fetch("/api/users/preferences", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.default_model_id) setValue(String(d.default_model_id))
      })
      .catch(() => {})
  }, [])

  const save = useCallback(
    async (v: string) => {
      const prev = value
      setValue(v)
      setPending(true)
      try {
        const r = await fetch("/api/users/preferences", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ default_model_id: v }),
        })
        if (!r.ok) throw new Error(`${r.status}`)
        toast.success("Модель по умолчанию сохранена")
      } catch {
        setValue(prev)
        toast.error("Не удалось сохранить")
      } finally {
        setPending(false)
      }
    },
    [value]
  )

  if (models === null) return <Spinner className="size-4" />
  if (models.length === 0)
    return <span className="text-sm text-muted-foreground">Недоступно</span>

  return (
    <Select value={value || undefined} disabled={pending} onValueChange={save}>
      <SelectTrigger className="w-56">
        <SelectValue placeholder="Выбрать модель" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          {models.map((m) => (
            <SelectItem key={m.id} value={m.id}>
              {m.label}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  )
}

// — Sessions / security —

interface SessionInfo {
  id: string
  expires: string
}

function SecurityControl() {
  const [count, setCount] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    fetch("/api/users/sessions", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : { sessions: [], count: 0 }))
      .then((d: { sessions: SessionInfo[]; count: number }) =>
        setCount(d.count)
      )
      .catch(() => setCount(null))
  }, [])

  useEffect(() => load(), [load])

  async function signOutEverywhere() {
    setBusy(true)
    try {
      await fetch("/api/users/sessions", { method: "DELETE" })
      await authClient.signOut()
      window.location.href = "/"
    } catch {
      toast.error("Не удалось выйти")
      setBusy(false)
    }
  }

  async function signOut() {
    setBusy(true)
    await authClient.signOut()
    window.location.href = "/"
  }

  return (
    <div className="flex flex-col">
      <Row
        label="Активные сессии"
        hint="Число активных входов в аккаунт. Детали устройств не сохраняются."
      >
        <span className="font-mono text-sm tabular-nums">{count ?? "—"}</span>
      </Row>
      <Row
        label="Выйти на всех устройствах"
        hint="Завершит все сессии, включая текущую."
      >
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={busy}
          onClick={signOutEverywhere}
        >
          {busy ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <ShieldCheck data-icon="inline-start" />
          )}
          Выйти везде
        </Button>
      </Row>
      <Row label="Текущая сессия" hint="Выйти из аккаунта на этом устройстве.">
        <Button type="button" size="sm" disabled={busy} onClick={signOut}>
          <LogOut data-icon="inline-start" />
          Выйти
        </Button>
      </Row>
    </div>
  )
}

// — View —

export function SettingsView({ account }: { account: SettingsAccount }) {
  const role = account.role ?? "student"

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-10 px-4 py-8">
      <Section title="Аккаунт">
        <div className="flex items-center gap-4 py-2">
          <Avatar className="size-12">
            <AvatarImage
              src={account.image ?? undefined}
              alt={account.name ?? ""}
            />
            <AvatarFallback>{initials(account.name)}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <p className="truncate font-semibold">
              {account.name ?? "Без имени"}
            </p>
            <p className="truncate text-sm text-muted-foreground">
              {account.email ?? "—"}
            </p>
          </div>
          <Badge className="ml-auto shrink-0">{ROLE_LABEL[role] ?? role}</Badge>
        </div>
      </Section>

      <Section title="Внешний вид">
        <Row label="Тема" hint="Светлая, тёмная или по настройке системы.">
          <ThemeControl />
        </Row>
      </Section>

      <Section title="Исследование">
        <Row
          label="Участие в исследовании"
          hint="Сбор обезличенных данных о действиях в лабораторной среде для адаптации обучения. Используется только в исследовательских целях."
        >
          <ConsentControl />
        </Row>
      </Section>

      <Section title="ИИ-модель">
        <Row
          label="Модель по умолчанию"
          hint="Подставляется при старте чата. Доступно при наличии права выбора модели."
        >
          <ModelControl />
        </Row>
      </Section>

      <Section title="Безопасность">
        <SecurityControl />
      </Section>
    </div>
  )
}
