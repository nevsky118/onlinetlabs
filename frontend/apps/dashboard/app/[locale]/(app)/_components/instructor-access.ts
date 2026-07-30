"use server"

import { hasInstructorAccess } from "@repo/auth/server"

/** Lives in the app because only the app can resolve the backend token. */
export async function fetchInstructorAccess(): Promise<boolean> {
  return hasInstructorAccess()
}
