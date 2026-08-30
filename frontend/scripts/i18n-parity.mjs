#!/usr/bin/env node
// Parity gate for the ru/en catalogs. next-intl renders the key itself instead of
// failing on a missing one, so a gap is otherwise only visible by eye.
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const scriptDir = dirname(fileURLToPath(import.meta.url))
const ruPath =
  process.argv[2] ?? join(scriptDir, "..", "packages/i18n/messages/ru.json")
const enPath =
  process.argv[3] ?? join(scriptDir, "..", "packages/i18n/messages/en.json")

const read = (file) => JSON.parse(readFileSync(file, "utf8"))

// Collapse a nested object into { "a.b.c": value }.
const flatten = (obj, prefix = "") => {
  const out = {}
  for (const [segment, value] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${segment}` : segment
    if (value && typeof value === "object" && !Array.isArray(value)) {
      Object.assign(out, flatten(value, key))
    } else {
      out[key] = value
    }
  }
  return out
}

// ICU arguments ({count}, {count, plural, ...}) and rich-text tags (<link>...</link>).
// An argument name is followed by "," or "}" ignoring spaces, which is what separates it
// from plural branch text such as "one {Checking...}".
const extractPlaceholders = (str) => {
  const set = new Set()
  for (const match of str.matchAll(/\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[,}]/g))
    set.add(match[1])
  for (const match of str.matchAll(/<\/?([a-zA-Z][a-zA-Z0-9]*)/g))
    set.add(match[1])
  return set
}

const ru = flatten(read(ruPath))
const en = flatten(read(enPath))
const ruKeys = Object.keys(ru)
const enKeys = Object.keys(en)

const missing = ruKeys.filter((key) => !(key in en))
const extra = enKeys.filter((key) => !(key in ru))

const placeholderMismatches = []
for (const key of ruKeys) {
  if (!(key in en)) continue
  const ruValue = ru[key]
  const enValue = en[key]
  if (typeof ruValue !== "string" || typeof enValue !== "string") continue
  const ruPlaceholders = extractPlaceholders(ruValue)
  const enPlaceholders = extractPlaceholders(enValue)
  const onlyInRu = [...ruPlaceholders].filter(
    (name) => !enPlaceholders.has(name)
  )
  const onlyInEn = [...enPlaceholders].filter(
    (name) => !ruPlaceholders.has(name)
  )
  if (onlyInRu.length || onlyInEn.length) {
    placeholderMismatches.push({ key, onlyInRu, onlyInEn })
  }
}

let failed = false

if (missing.length) {
  failed = true
  console.error(`MISSING IN en.json (${missing.length}):`)
  for (const key of missing) console.error(`  ${key}`)
}

if (extra.length) {
  failed = true
  console.error(`EXTRA IN en.json (${extra.length}):`)
  for (const key of extra) console.error(`  ${key}`)
}

if (placeholderMismatches.length) {
  failed = true
  console.error(`PLACEHOLDER MISMATCH (${placeholderMismatches.length}):`)
  for (const { key, onlyInRu, onlyInEn } of placeholderMismatches) {
    console.error(`  ${key}`)
    if (onlyInRu.length) console.error(`    only in ru: ${onlyInRu.join(", ")}`)
    if (onlyInEn.length) console.error(`    only in en: ${onlyInEn.join(", ")}`)
  }
}

// The platform stores pseudonymous data, not anonymous data. A string that says
// otherwise is a false consent claim, so it fails the build rather than shipping.
// web.privacy is exempt: it exists to say the data is NOT anonymous.
const ANONYMITY = /anonymi[sz]|обезличен|анонимн/i
const claims = []
for (const key of ruKeys) {
  if (key.startsWith("web.privacy")) continue
  for (const [catalogLocale, catalog] of [
    ["ru", ru],
    ["en", en],
  ]) {
    const value = catalog[key]
    if (typeof value === "string" && ANONYMITY.test(value)) {
      claims.push(`  ${catalogLocale} ${key}: ${value.slice(0, 80)}`)
    }
  }
}
if (claims.length) {
  failed = true
  console.error(
    `ANONYMITY CLAIM (${claims.length}) -- data is pseudonymous, not anonymous:`
  )
  for (const claim of claims) console.error(claim)
}

if (failed) process.exit(1)
console.log(
  `i18n parity ok (${ruKeys.length} keys, placeholders match, no anonymity claims)`
)
