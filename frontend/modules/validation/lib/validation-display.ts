import type { ValidationCheck } from "../types"

export function formatDuration(ms: number | null): string {
  if (ms === null) return ""
  if (ms < 1000) return `${ms} мс`
  const sec = ms / 1000
  if (sec < 60) return `${sec.toFixed(1)} с`
  const min = Math.floor(sec / 60)
  const rem = Math.round(sec % 60)
  return rem > 0 ? `${min} мин ${rem} с` : `${min} мин`
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
    .map(([k, v]) => `${k}=${String(v)}`)
    .join(", ")
  return `${kind}(${paramStr})`
}
