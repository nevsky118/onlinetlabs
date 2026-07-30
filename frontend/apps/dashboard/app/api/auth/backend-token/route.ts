import {
  BackendUnavailableError,
  getBackendToken,
  getSession,
} from "@repo/auth/server"
import { NextResponse } from "next/server"

export async function GET() {
  const session = await getSession()
  if (!session?.user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 })
  }
  try {
    const token = await getBackendToken()
    if (!token) {
      return NextResponse.json({ error: "no token" }, { status: 401 })
    }
    return NextResponse.json({ token })
  } catch (error) {
    // A transient backend failure ≠ a logout. 503, the client will retry.
    if (error instanceof BackendUnavailableError) {
      return NextResponse.json(
        { error: "backend unavailable" },
        { status: 503 }
      )
    }
    throw error
  }
}
