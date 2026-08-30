#!/usr/bin/env node
// Snapshot of the Tailwind classes generated into the built CSS.
// Catches a silently broken @source, where the build passes but no classes are emitted.
//   node scripts/css-classes.mjs <appDir> > baseline.css.json
//   node scripts/css-classes.mjs <appDir> --check baseline.css.json
import { readFileSync, existsSync, readdirSync, statSync } from "node:fs"
import { join } from "node:path"

const appDir = process.argv[2]
if (!appDir) {
  console.error("usage: css-classes.mjs <appDir> [--check <baseline.json>]")
  process.exit(2)
}

const walk = (dir, out = []) => {
  if (!existsSync(dir)) return out
  for (const entry of readdirSync(dir)) {
    // dev/ holds dev-server artifacts, which turbo also excludes from outputs.
    // node_modules is a copied tree under output:"standalone" with broken symlinks.
    if (entry === "cache" || entry === "dev" || entry === "node_modules")
      continue
    const entryPath = join(dir, entry)
    let stats
    try {
      stats = statSync(entryPath)
    } catch {
      continue // dangling symlink
    }
    if (stats.isDirectory()) walk(entryPath, out)
    else if (entry.endsWith(".css")) out.push(entryPath)
  }
  return out
}

const files = walk(join(appDir, ".next"))
if (files.length === 0) {
  console.error(`no built css under ${appDir}/.next — run a build first`)
  process.exit(2)
}

// Comments are stripped because sourceMappingURL yields fake .css/.map classes from file names.
const css = files
  .map((file) => readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\//g, ""))
  .join("\n")
// Class selectors, including escaped ones (.md\:flex, .bg-primary/50 and so on).
const classes = new Set()
for (const match of css.matchAll(/\.((?:\\.|[-\w])+)/g)) {
  const name = match[1].replace(/\\/g, "")
  if (name.length > 1) classes.add(name)
}

const sorted = classes.values().toArray().toSorted()
const checkIdx = process.argv.indexOf("--check")
if (checkIdx === -1) {
  console.log(
    JSON.stringify({ count: sorted.length, classes: sorted }, null, 2)
  )
  process.exit(0)
}

const base = JSON.parse(readFileSync(process.argv[checkIdx + 1], "utf8"))
const before = new Set(base.classes)
const missing = base.classes.filter((name) => !classes.has(name))
const added = sorted.filter((name) => !before.has(name))

if (missing.length) {
  console.error(`CSS CLASSES LOST: ${missing.length} of ${base.count}`)
  for (const name of missing.slice(0, 40)) console.error(`  -${name}`)
  if (missing.length > 40)
    console.error(`  ... and ${missing.length - 40} more`)
  process.exit(1)
}
console.log(
  `css ok: ${sorted.length} classes, none lost (+${added.length} new)`
)
