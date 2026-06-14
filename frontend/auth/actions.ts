"use server"

import { hasInstructorAccess } from "./role"

export async function fetchInstructorAccess(): Promise<boolean> {
  return hasInstructorAccess()
}
