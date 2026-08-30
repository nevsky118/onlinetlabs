import { parseAsString } from "nuqs"

// No default: an absent ?redirect must stay null so the caller falls back to the
// locale-aware destination. A default of "/" silently won that choice and sent
// every sign-in to the bare root.
export const redirectParser = parseAsString
