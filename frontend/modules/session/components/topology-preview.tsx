"use client"

import { useMemo } from "react"
import type { Link, Node } from "../types"

function statusColor(status: Node["status"]) {
  switch (status) {
    case "started":
      return "stroke-emerald-500"
    case "stopped":
      return "stroke-muted-foreground"
    case "suspended":
      return "stroke-amber-500"
  }
}

export function TopologyPreview({
  nodes,
  links,
}: {
  nodes: Node[]
  links: Link[]
}) {
  const positions = useMemo(() => {
    const radius = 60
    const cx = 100
    const cy = 80
    const map: Record<string, { x: number; y: number }> = {}
    const count = Math.max(1, nodes.length)
    nodes.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / count
      map[n.id] = {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      }
    })
    return map
    // recompute only when set of node ids changes
  }, [nodes.map((n) => n.id).join("|")])

  if (nodes.length === 0) {
    return (
      <div className="text-muted-foreground text-xs">Узлы не настроены</div>
    )
  }

  return (
    <svg
      viewBox="0 0 200 160"
      className="w-full"
      aria-label="Live-топология сессии"
    >
      {links.map((l) => {
        const a = l.nodes[0] ? positions[l.nodes[0].nodeId] : undefined
        const b = l.nodes[1] ? positions[l.nodes[1].nodeId] : undefined
        if (!a || !b) return null
        return (
          <line
            key={l.id}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            className="stroke-muted-foreground"
            strokeDasharray="3 2"
          />
        )
      })}
      {nodes.map((n) => {
        const p = positions[n.id]
        if (!p) return null
        return (
          <g key={n.id} className="transition-all">
            <circle
              cx={p.x}
              cy={p.y}
              r="14"
              className={`fill-card ${statusColor(n.status)}`}
              strokeWidth="1.5"
            />
            <text
              x={p.x}
              y={p.y + 3}
              textAnchor="middle"
              fontFamily="monospace"
              fontSize="9"
              className="fill-foreground"
            >
              {n.name}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
