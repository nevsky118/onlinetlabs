import { headers } from "next/headers"
import { cache, type ReactNode } from "react"
import { auth } from "@/shared/auth"

export const getSession = cache(async () => {
  return auth.api.getSession({ headers: await headers() })
})

export async function SignedIn({ children }: { children: ReactNode }) {
  const session = await getSession()
  if (!session?.user) return null
  return <>{children}</>
}

export async function SignedOut({ children }: { children: ReactNode }) {
  const session = await getSession()
  if (session?.user) return null
  return <>{children}</>
}
