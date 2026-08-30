#!/usr/bin/env node
// Snapshot of the app routes taken from next build artifacts.
import { readFileSync, existsSync } from "node:fs"
import { join } from "node:path"

const appDir = process.argv[2]
if (!appDir) {
  console.error("usage: route-manifest.mjs <appDir> [--check <baseline.json>]")
  process.exit(2)
}

const read = (file) => JSON.parse(readFileSync(file, "utf8"))
const next = join(appDir, ".next")
const appPaths = join(next, "app-path-routes-manifest.json")
const prerender = join(next, "prerender-manifest.json")

for (const file of [appPaths, prerender]) {
  if (!existsSync(file)) {
    console.error(`missing ${file} — run \`next build\` first`)
    process.exit(2)
  }
}

const routes = [...new Set(Object.values(read(appPaths)))]
const pre = read(prerender)
const staticRoutes = new Set(Object.keys(pre.routes ?? {}))
const isrRoutes = new Set(Object.keys(pre.dynamicRoutes ?? {}))

const manifest = {}
for (const route of routes.toSorted()) {
  manifest[route] = route.startsWith("/api/")
    ? "handler"
    : staticRoutes.has(route)
      ? "static"
      : isrRoutes.has(route)
        ? "prerender-params"
        : "dynamic"
}
// Concrete prerendered paths (/labs/dhcp-basics) never show up in the route list.
for (const route of staticRoutes.values().toArray().toSorted()) {
  if (!(route in manifest)) manifest[route] = "static"
}

const checkIdx = process.argv.indexOf("--check")
if (checkIdx === -1) {
  console.log(JSON.stringify(manifest, null, 2))
  process.exit(0)
}

const baseline = read(process.argv[checkIdx + 1])
const diffs = []
for (const route of new Set([
  ...Object.keys(baseline),
  ...Object.keys(manifest),
])) {
  if (baseline[route] !== manifest[route]) {
    diffs.push(
      `${route}: ${baseline[route] ?? "(absent)"} -> ${manifest[route] ?? "(gone)"}`
    )
  }
}
if (diffs.length) {
  console.error(`ROUTE PARITY BROKEN (${diffs.length}):`)
  for (const diff of diffs.toSorted()) console.error(`  ${diff}`)
  process.exit(1)
}
console.log(`route parity ok (${Object.keys(manifest).length} entries)`)
