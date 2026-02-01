import { NextProvider } from "fumadocs-core/framework/next"
import type { ReactNode } from "react"

export function FumadocsProvider({ children }: { children: ReactNode }) {
  // or if you're using Fumadocs UI, use `<RootProvider />`
  return <NextProvider>{children}</NextProvider>
}
