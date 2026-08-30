"use client"

import { useTranslations } from "next-intl"
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

const RADIUS = 60
const CENTER_X = 100
const CENTER_Y = 80

// oxlint-disable-next-line eslint/id-length -- x/y are the SVG coordinate names
type Point = { x: number; y: number }

/** Lays the nodes out on a circle, in the order they arrive. */
function layoutOnCircle(nodeIds: string[]): Record<string, Point> {
  const count = Math.max(1, nodeIds.length)
  const positions: Record<string, Point> = {}
  nodeIds.forEach((nodeId, index) => {
    const angle = (2 * Math.PI * index) / count
    positions[nodeId] = {
      x: CENTER_X + RADIUS * Math.cos(angle),
      y: CENTER_Y + RADIUS * Math.sin(angle),
    }
  })
  return positions
}

export function TopologyPreview({
  nodes,
  links,
}: {
  nodes: Node[]
  links: Link[]
}) {
  const t = useTranslations("dashboard.session.topologyPreview")
  // Keyed on the id list so a status-only update keeps the same layout.
  const nodeIdKey = nodes.map((node) => node.id).join("|")
  const positions = useMemo(
    () => layoutOnCircle(nodeIdKey ? nodeIdKey.split("|") : []),
    [nodeIdKey]
  )

  if (nodes.length === 0) {
    return <div className="text-xs text-muted-foreground">{t("empty")}</div>
  }

  return (
    <svg viewBox="0 0 200 160" className="w-full" aria-label={t("ariaLabel")}>
      {links.map((link) => {
        const from = link.nodes[0] ? positions[link.nodes[0].nodeId] : undefined
        const to = link.nodes[1] ? positions[link.nodes[1].nodeId] : undefined
        if (!from || !to) return null
        return (
          <line
            key={link.id}
            x1={from.x}
            y1={from.y}
            x2={to.x}
            y2={to.y}
            className="stroke-muted-foreground"
            strokeDasharray="3 2"
          />
        )
      })}
      {nodes.map((node) => {
        const position = positions[node.id]
        if (!position) return null
        return (
          <g key={node.id} className="transition-all">
            <circle
              cx={position.x}
              cy={position.y}
              r="14"
              className={`fill-card ${statusColor(node.status)}`}
              strokeWidth="1.5"
            />
            <text
              x={position.x}
              y={position.y + 3}
              textAnchor="middle"
              fontFamily="monospace"
              fontSize="9"
              className="fill-foreground"
            >
              {node.name}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
