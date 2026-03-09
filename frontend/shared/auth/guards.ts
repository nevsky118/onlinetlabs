import { forbidden, unauthorized } from "next/navigation"
import type { Role } from "./permissions"
import { getSession } from "./session"
import { auth } from "@/shared/auth"

export async function requireAuth() {
  const session = await getSession()
  if (!session?.user) return unauthorized()
  return session
}

export async function requireRole(allowedRoles: Role[]) {
  const session = await requireAuth()
  const userRole = (session.user as { role?: string }).role
  if (!userRole || !allowedRoles.includes(userRole as Role)) return forbidden()
  return session
}

export async function requirePermission(resource: string, actions: string[]) {
  const session = await requireAuth()

  const result = await auth.api.userHasPermission({
    body: {
      userId: session.user.id,
      permission: { [resource]: actions },
    },
  })

  if (!result.success) return forbidden()
  return session
}
