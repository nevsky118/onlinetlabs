#!/usr/bin/env node
// Parity gate for the ru/en catalogs. next-intl renders the key itself instead of
// failing on a missing one, so a gap is otherwise only visible by eye.
import { readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { join, dirname } from "node:path"

const scriptDir = dirname(fileURLToPath(import.meta.url))
const ruPath = process.argv[2] ?? join(scriptDir, "..", "packages/i18n/messages/ru.json")
const enPath = process.argv[3] ?? join(scriptDir, "..", "packages/i18n/messages/en.json")

const read = (p) => JSON.parse(readFileSync(p, "utf8"))

// Collapse a nested object into { "a.b.c": value }.
const flatten = (obj, prefix = "") => {
  const out = {}
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === "object" && !Array.isArray(v)) {
      Object.assign(out, flatten(v, key))
    } else {
      out[key] = v
    }
  }
  return out
}

// ICU arguments ({count}, {count, plural, ...}) and rich-text tags (<link>...</link>).
// An argument name is followed by "," or "}" ignoring spaces, which is what separates it
// from plural branch text such as "one {Checking...}".
const extractPlaceholders = (str) => {
  const set = new Set()
  for (const m of str.matchAll(/\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[,}]/g)) set.add(m[1])
  for (const m of str.matchAll(/<\/?([a-zA-Z][a-zA-Z0-9]*)/g)) set.add(m[1])
  return set
}

const ru = flatten(read(ruPath))
const en = flatten(read(enPath))
const ruKeys = Object.keys(ru)
const enKeys = Object.keys(en)

const missing = ruKeys.filter((k) => !(k in en))
const extra = enKeys.filter((k) => !(k in ru))

const placeholderMismatches = []
for (const k of ruKeys) {
  if (!(k in en)) continue
  const ruVal = ru[k]
  const enVal = en[k]
  if (typeof ruVal !== "string" || typeof enVal !== "string") continue
  const ruPh = extractPlaceholders(ruVal)
  const enPh = extractPlaceholders(enVal)
  const onlyInRu = [...ruPh].filter((p) => !enPh.has(p))
  const onlyInEn = [...enPh].filter((p) => !ruPh.has(p))
  if (onlyInRu.length || onlyInEn.length) {
    placeholderMismatches.push({ key: k, onlyInRu, onlyInEn })
  }
}

let failed = false

if (missing.length) {
  failed = true
  console.error(`MISSING IN en.json (${missing.length}):`)
  for (const k of missing) console.error(`  ${k}`)
}

if (extra.length) {
  failed = true
  console.error(`EXTRA IN en.json (${extra.length}):`)
  for (const k of extra) console.error(`  ${k}`)
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
  for (const [loc, flat] of [["ru", ru], ["en", en]]) {
    const value = flat[key]
    if (typeof value === "string" && ANONYMITY.test(value)) {
      claims.push(`  ${loc} ${key}: ${value.slice(0, 80)}`)
    }
  }
}
if (claims.length) {
  failed = true
  console.error(`ANONYMITY CLAIM (${claims.length}) -- data is pseudonymous, not anonymous:`)
  for (const c of claims) console.error(c)
}

if (failed) process.exit(1)
console.log(`i18n parity ok (${ruKeys.length} keys, placeholders match, no anonymity claims)`)
