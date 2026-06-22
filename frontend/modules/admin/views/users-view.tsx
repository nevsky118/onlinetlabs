"use client"

import { useRouter } from "next/navigation"
import { useQueryStates } from "nuqs"
import { useCallback, useEffect, useRef, useState } from "react"
import { toast } from "sonner"
import type { AdminUser, AdminUsersPage, UserRole } from "../types"
import { updateAdminUser } from "../actions"
import { parsers } from "../lib/users-search-params"
import { cn } from "@/shared/lib/utils"
import { Alert, AlertDescription, AlertTitle } from "@/ui/alert"
import { Input } from "@/ui/input"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/ui/select"
import { Skeleton } from "@/ui/skeleton"
import { Switch } from "@/ui/switch"

interface UsersViewProps {
  data: AdminUsersPage | null
  error: string | null
  currentUserId: string | null
}

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: "student", label: "Студент" },
  { value: "instructor", label: "Инструктор" },
  { value: "admin", label: "Администратор" },
]

function SortIcon({ active, dir }: { active: boolean; dir: "asc" | "desc" }) {
  if (!active) return <span className="ml-1 opacity-30">↕</span>
  return <span className="ml-1">{dir === "asc" ? "↑" : "↓"}</span>
}

function UserRow({
  user,
  isSelf,
  onUpdate,
}: {
  user: AdminUser
  isSelf: boolean
  onUpdate: (
    id: string,
    patch: Partial<
      Pick<AdminUser, "role" | "canSelectModel" | "canViewAgentLogs">
    >
  ) => Promise<void>
}) {
  const [pending, setPending] = useState(false)

  const handle = async (
    patch: Partial<
      Pick<AdminUser, "role" | "canSelectModel" | "canViewAgentLogs">
    >
  ) => {
    setPending(true)
    try {
      await onUpdate(user.id, patch)
    } finally {
      setPending(false)
    }
  }

  return (
    <tr className={cn("border-b border-border", pending && "opacity-60")}>
      <td className="py-3 pr-4">
        <div className="flex items-center gap-3">
          {user.image ? (
            // biome-ignore lint/performance/noImgElement: avatar from trusted backend, no Next/Image needed
            <img
              src={user.image}
              alt=""
              className="size-8 shrink-0 object-cover"
              aria-hidden
            />
          ) : (
            <div className="size-8 shrink-0 bg-muted" />
          )}
          <span className="truncate font-medium text-sm">{user.name}</span>
        </div>
      </td>
      <td className="py-3 pr-4 text-muted-foreground text-sm truncate max-w-[200px]">
        {user.email}
      </td>
      <td className="py-3 pr-4">
        <Select
          value={user.role}
          onValueChange={(v) => handle({ role: v as UserRole })}
          disabled={isSelf || pending}
        >
          <SelectTrigger
            size="sm"
            className="w-36"
            title={isSelf ? "Нельзя менять свою роль" : undefined}
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {ROLE_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </td>
      <td className="py-3 pr-4">
        <Switch
          size="sm"
          checked={user.canSelectModel}
          onCheckedChange={(v) => handle({ canSelectModel: v })}
          disabled={pending}
          aria-label="Выбор модели"
        />
      </td>
      <td className="py-3">
        <Switch
          size="sm"
          checked={user.canViewAgentLogs}
          onCheckedChange={(v) => handle({ canViewAgentLogs: v })}
          disabled={pending}
          aria-label="Логи агентов"
        />
      </td>
    </tr>
  )
}

export function UsersView({ data, error, currentUserId }: UsersViewProps) {
  const router = useRouter()
  const [params, setParams] = useQueryStates(parsers)
  const [localSearch, setLocalSearch] = useState(params.search)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [users, setUsers] = useState<AdminUser[]>(data?.items ?? [])

  // sync server-rendered items into local state
  useEffect(() => {
    setUsers(data?.items ?? [])
  }, [data])

  const handleSearchChange = useCallback(
    (val: string) => {
      setLocalSearch(val)
      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => {
        setParams({ search: val, page: 1 })
      }, 400)
    },
    [setParams]
  )

  const toggleSort = useCallback(
    (col: "name" | "email" | "role") => {
      if (params.sort === col) {
        setParams({ order: params.order === "asc" ? "desc" : "asc", page: 1 })
      } else {
        setParams({ sort: col, order: "asc", page: 1 })
      }
    },
    [params.sort, params.order, setParams]
  )

  const handleUpdate = useCallback(
    async (
      id: string,
      patch: Partial<
        Pick<AdminUser, "role" | "canSelectModel" | "canViewAgentLogs">
      >
    ) => {
      const result = await updateAdminUser(id, patch)
      if (result.ok) {
        setUsers((prev) => prev.map((u) => (u.id === id ? result.user : u)))
        toast.success("Сохранено")
        router.refresh()
      } else {
        toast.error(result.error)
      }
    },
    [router]
  )

  const total = data?.total ?? 0
  const pageSize = params.pageSize
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="flex flex-col gap-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Input
          type="search"
          placeholder="Поиск по имени / email"
          value={localSearch}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="max-w-xs"
        />
        <Select
          value={params.role ?? "all"}
          onValueChange={(v) =>
            setParams({ role: v === "all" ? null : (v as UserRole), page: 1 })
          }
        >
          <SelectTrigger size="sm" className="w-44">
            <SelectValue placeholder="Все роли" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem value="all">Все роли</SelectItem>
              {ROLE_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>

      {/* Error */}
      {error && (
        <Alert variant="destructive">
          <AlertTitle>Ошибка</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Skeleton */}
      {!data && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={`skel-${i}`} className="h-12 w-full" />
          ))}
        </div>
      )}

      {/* Table */}
      {data && (
        <>
          {users.length === 0 ? (
            <p className="py-8 text-center text-muted-foreground text-sm">
              Пользователи не найдены
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="py-2 pr-4 text-left font-medium">
                      <button
                        type="button"
                        className="inline-flex items-center"
                        onClick={() => toggleSort("name")}
                      >
                        Пользователь
                        <SortIcon
                          active={params.sort === "name"}
                          dir={params.order}
                        />
                      </button>
                    </th>
                    <th className="py-2 pr-4 text-left font-medium">
                      <button
                        type="button"
                        className="inline-flex items-center"
                        onClick={() => toggleSort("email")}
                      >
                        Email
                        <SortIcon
                          active={params.sort === "email"}
                          dir={params.order}
                        />
                      </button>
                    </th>
                    <th className="py-2 pr-4 text-left font-medium">
                      <button
                        type="button"
                        className="inline-flex items-center"
                        onClick={() => toggleSort("role")}
                      >
                        Роль
                        <SortIcon
                          active={params.sort === "role"}
                          dir={params.order}
                        />
                      </button>
                    </th>
                    <th className="py-2 pr-4 text-left font-medium">
                      Выбор модели
                    </th>
                    <th className="py-2 text-left font-medium">Логи агентов</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <UserRow
                      key={user.id}
                      user={user}
                      isSelf={user.id === currentUserId}
                      onUpdate={handleUpdate}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          <div className="flex items-center justify-between text-sm tabular-nums">
            <span className="text-muted-foreground">Всего: {total}</span>
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="px-2 py-1 border border-border disabled:opacity-40"
                disabled={params.page <= 1}
                onClick={() => setParams({ page: params.page - 1 })}
              >
                ←
              </button>
              <span>
                стр. {params.page} из {totalPages}
              </span>
              <button
                type="button"
                className="px-2 py-1 border border-border disabled:opacity-40"
                disabled={params.page >= totalPages}
                onClick={() => setParams({ page: params.page + 1 })}
              >
                →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
