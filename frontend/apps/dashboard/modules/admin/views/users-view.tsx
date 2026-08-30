"use client"

import { cn } from "@repo/design-system/lib/utils"
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@repo/design-system/ui/alert"
import { Input } from "@repo/design-system/ui/input"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@repo/design-system/ui/select"
import { Skeleton } from "@repo/design-system/ui/skeleton"
import { Switch } from "@repo/design-system/ui/switch"
import { useTranslations } from "next-intl"
import { useRouter } from "next/navigation"
import { useQueryStates } from "nuqs"
import { useCallback, useRef, useState } from "react"
import { toast } from "sonner"
import type { AdminUser, AdminUsersPage, UserRole } from "../types"
import { updateAdminUser } from "../actions"
import { parsers } from "../lib/users-search-params"

interface UsersViewProps {
  data: AdminUsersPage | null
  error: string | null
  currentUserId: string | null
}

function getRoleOptions(
  t: (key: string) => string
): { value: UserRole; label: string }[] {
  return [
    { value: "student", label: t("roles.student") },
    { value: "instructor", label: t("roles.instructor") },
    { value: "admin", label: t("roles.admin") },
  ]
}

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
      Pick<
        AdminUser,
        "role" | "isActive" | "canSelectModel" | "canViewAgentLogs"
      >
    >
  ) => Promise<void>
}) {
  const t = useTranslations("dashboard.admin.users")
  const [pending, setPending] = useState(false)

  const handle = async (
    patch: Partial<
      Pick<
        AdminUser,
        "role" | "isActive" | "canSelectModel" | "canViewAgentLogs"
      >
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
            // oxlint-disable-next-line nextjs/no-img-element -- avatar URL comes from the backend, no next/image loader needed
            <img
              src={user.image}
              alt=""
              className="size-8 shrink-0 object-cover"
              aria-hidden
            />
          ) : (
            <div className="size-8 shrink-0 bg-muted" />
          )}
          <span className="truncate text-sm font-medium">{user.name}</span>
        </div>
      </td>
      <td className="max-w-[200px] truncate py-3 pr-4 text-sm text-muted-foreground">
        {user.email}
      </td>
      <td className="py-3 pr-4">
        <Select
          value={user.role}
          onValueChange={(role) => handle({ role: role as UserRole })}
          disabled={isSelf || pending}
        >
          <SelectTrigger
            size="sm"
            className="w-36"
            title={isSelf ? t("cannotChangeOwnRole") : undefined}
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {getRoleOptions(t).map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </td>
      <td className="py-3 pr-4">
        <Switch
          size="sm"
          checked={user.isActive}
          onCheckedChange={(checked) => handle({ isActive: checked })}
          disabled={pending}
          aria-label={t("ariaActive")}
        />
      </td>
      <td className="py-3 pr-4">
        <Switch
          size="sm"
          checked={user.canSelectModel}
          onCheckedChange={(checked) => handle({ canSelectModel: checked })}
          disabled={pending}
          aria-label={t("ariaModelSelect")}
        />
      </td>
      <td className="py-3">
        <Switch
          size="sm"
          checked={user.canViewAgentLogs}
          onCheckedChange={(checked) => handle({ canViewAgentLogs: checked })}
          disabled={pending}
          aria-label={t("ariaAgentLogs")}
        />
      </td>
    </tr>
  )
}

export function UsersView({ data, error, currentUserId }: UsersViewProps) {
  const t = useTranslations("dashboard.admin.users")
  const router = useRouter()
  const [params, setParams] = useQueryStates(parsers)
  const [localSearch, setLocalSearch] = useState(params.search)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [users, setUsers] = useState<AdminUser[]>(data?.items ?? [])
  // Sync the server-rendered items during render, not in an effect.
  const [syncedData, setSyncedData] = useState(data)
  if (data !== syncedData) {
    setSyncedData(data)
    setUsers(data?.items ?? [])
  }

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
        Pick<
          AdminUser,
          "role" | "isActive" | "canSelectModel" | "canViewAgentLogs"
        >
      >
    ) => {
      const result = await updateAdminUser(id, patch)
      if (result.ok) {
        setUsers((prev) =>
          prev.map((user) => (user.id === id ? result.user : user))
        )
        toast.success(t("toastSaved"))
        router.refresh()
      } else {
        toast.error(result.error)
      }
    },
    [router, t]
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
          placeholder={t("searchPlaceholder")}
          value={localSearch}
          onChange={(event) => handleSearchChange(event.target.value)}
          className="max-w-xs"
        />
        <Select
          value={params.role ?? "all"}
          onValueChange={(value) =>
            setParams({
              role: value === "all" ? null : (value as UserRole),
              page: 1,
            })
          }
        >
          <SelectTrigger size="sm" className="w-44">
            <SelectValue placeholder={t("allRoles")} />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem value="all">{t("allRoles")}</SelectItem>
              {getRoleOptions(t).map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>

      {/* Error */}
      {error && (
        <Alert variant="destructive">
          <AlertTitle>{t("errorTitle")}</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Skeleton */}
      {!data && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={`skel-${index}`} className="h-12 w-full" />
          ))}
        </div>
      )}

      {/* Table */}
      {data && (
        <>
          {users.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              {t("empty")}
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
                        {t("headers.user")}
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
                        {t("headers.role")}
                        <SortIcon
                          active={params.sort === "role"}
                          dir={params.order}
                        />
                      </button>
                    </th>
                    <th className="py-2 pr-4 text-left font-medium">
                      {t("headers.active")}
                    </th>
                    <th className="py-2 pr-4 text-left font-medium">
                      {t("headers.modelSelect")}
                    </th>
                    <th className="py-2 text-left font-medium">
                      {t("headers.agentLogs")}
                    </th>
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
            <span className="text-muted-foreground">
              {t("total", { count: total })}
            </span>
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="border border-border px-2 py-1 disabled:opacity-40"
                disabled={params.page <= 1}
                onClick={() => setParams({ page: params.page - 1 })}
              >
                ←
              </button>
              <span>
                {t("pageOf", { page: params.page, total: totalPages })}
              </span>
              <button
                type="button"
                className="border border-border px-2 py-1 disabled:opacity-40"
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
