import { type Locale, routing } from "./routing"

type MessageTree = { [key: string]: unknown }

const catalogs: Record<Locale, () => Promise<{ default: MessageTree }>> = {
  en: () => import("./messages/en.json"),
  ru: () => import("./messages/ru.json"),
}

function isLocale(value: string): value is Locale {
  return (routing.locales as readonly string[]).includes(value)
}

function readNamespace(
  catalog: MessageTree,
  path: string[]
): unknown | undefined {
  let node: unknown = catalog
  for (const segment of path) {
    if (typeof node !== "object" || node === null) return undefined
    node = (node as MessageTree)[segment]
  }
  return node
}

/** Narrows the catalog to the namespaces a client tree may serialize. */
export async function pickMessages(
  locale: string,
  namespaces: readonly string[]
): Promise<MessageTree> {
  const load = catalogs[isLocale(locale) ? locale : routing.defaultLocale]
  const catalog = (await load()).default
  const picked: MessageTree = {}

  for (const namespace of namespaces) {
    const path = namespace.split(".")
    const leaf = path[path.length - 1]
    const value = readNamespace(catalog, path)
    if (value === undefined) continue

    let branch = picked
    for (const segment of path.slice(0, -1)) {
      branch[segment] ??= {}
      branch = branch[segment] as MessageTree
    }
    branch[leaf] = value
  }

  return picked
}
