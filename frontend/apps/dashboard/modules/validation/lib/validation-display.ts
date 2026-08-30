import { formatPreciseDuration } from "@/lib/format-duration"
import type { ValidationCheck } from "../types"

export function formatDuration(
  ms: number | null,
  t: (key: string, values?: Record<string, number>) => string
): string {
  if (ms === null) return ""
  return formatPreciseDuration(ms, t)
}

export function commandFor(check: ValidationCheck): string {
  const { kind, params } = check
  if (kind === "vpcs.show_ip") return "show ip"
  if (kind === "vpcs.ping") {
    const to = params.to ? String(params.to) : ""
    return `ping ${to}`.trim()
  }
  if (kind === "frr.ospf_neighbor") return "show ip ospf neighbor"
  if (kind === "frr.ospf_routes") return "show ip ospf route"
  if (kind === "frr.interfaces") return "show interface brief"
  // generic fallback: kind(params)
  const paramStr = Object.entries(params)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join(", ")
  return `${kind}(${paramStr})`
}
