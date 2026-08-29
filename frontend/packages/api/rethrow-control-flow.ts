import { unstable_rethrow } from "next/navigation"

/** Rethrows Next control-flow errors (redirect, notFound) so a catch cannot swallow them. */
export function rethrowControlFlow(error: unknown): void {
  unstable_rethrow(error)
}
