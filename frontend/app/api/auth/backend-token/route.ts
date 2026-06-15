import { NextResponse } from "next/server"
import { getSession } from "@/auth/session"
import { BackendUnavailableError, getBackendToken } from "@/auth/token"

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
    // Транзиентный сбой backend ≠ разлогин: 503, клиент повторит.
    if (error instanceof BackendUnavailableError) {
      return NextResponse.json(
        { error: "backend unavailable" },
        { status: 503 }
      )
    }
    throw error
  }
}
