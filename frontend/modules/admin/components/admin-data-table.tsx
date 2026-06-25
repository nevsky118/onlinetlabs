"use client"

import { useQueryStates } from "nuqs"
import { useCallback, useRef, useState } from "react"
import type { AdminDataPage, AdminDataRow } from "../types"
import { parsers } from "../lib/data-table-params"
import { cn } from "@/lib/utils"
import { Alert, AlertDescription, AlertTitle } from "@/ui/alert"
import { Input } from "@/ui/input"
import { Skeleton } from "@/ui/skeleton"

interface AdminDataTableProps {
  data: AdminDataPage | null
  error: string | null
}

function SortIcon({ active, dir }: { active: boolean; dir: "asc" | "desc" }) {
  if (!active) return <span className="ml-1 opacity-30">↕</span>
  return <span className="ml-1">{dir === "asc" ? "↑" : "↓"}</span>
}

function formatCell(value: unknown): React.ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground">—</span>
  }
  if (typeof value === "boolean") {
    return value ? "да" : "нет"
  }
  if (typeof value === "number") {
    return <span className="tabular-nums">{value}</span>
  }
  if (typeof value === "object") {
    const s = JSON.stringify(value)
    const truncated = s.length > 80 ? `${s.slice(0, 80)}…` : s
    return (
      <span title={s} className="font-mono text-xs">
        {truncated}
      </span>
    )
  }
  const s = String(value)
  return (
    <span title={s} className="max-w-[260px] truncate block">
      {s}
    </span>
  )
}

export function AdminDataTable({ data, error }: AdminDataTableProps) {
  const [params, setParams] = useQueryStates(parsers)
  const [localSearch, setLocalSearch] = useState(params.search)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

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
    (col: string) => {
      if (params.sort === col) {
        setParams({ order: params.order === "asc" ? "desc" : "asc", page: 1 })
      } else {
        setParams({ sort: col, order: "asc", page: 1 })
      }
    },
    [params.sort, params.order, setParams]
  )

  const total = data?.total ?? 0
  const pageSize = params.pageSize
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="flex flex-col gap-4">
      {/* Search */}
      <div className="flex flex-wrap gap-3">
        <Input
          type="search"
          placeholder="Поиск..."
          value={localSearch}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="max-w-xs"
        />
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
          {data.items.length === 0 ? (
            <p className="py-8 text-center text-muted-foreground text-sm">
              Нет записей
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {data.columns.map((col) => (
                      <th
                        key={col}
                        className="py-2 pr-4 text-left font-medium whitespace-nowrap"
                      >
                        {data.sortable.includes(col) ? (
                          <button
                            type="button"
                            className="inline-flex items-center"
                            onClick={() => toggleSort(col)}
                          >
                            {col}
                            <SortIcon
                              active={params.sort === col}
                              dir={params.order}
                            />
                          </button>
                        ) : (
                          col
                        )}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((row: AdminDataRow, ri) => (
                    <tr key={ri} className="border-b border-border">
                      {data.columns.map((col) => (
                        <td key={col} className="py-3 pr-4 align-top">
                          {formatCell(row[col])}
                        </td>
                      ))}
                    </tr>
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
                className={cn(
                  "px-2 py-1 border border-border",
                  params.page <= 1 && "opacity-40"
                )}
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
                className={cn(
                  "px-2 py-1 border border-border",
                  params.page >= totalPages && "opacity-40"
                )}
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
