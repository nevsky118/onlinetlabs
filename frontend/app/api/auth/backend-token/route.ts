import { NextResponse } from "next/server"
import { getSession } from "@/auth/session"
import { getBackendToken } from "@/auth/token"

export async function GET() {
  const session = await getSession()
  if (!session?.user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 })
  }
  const token = await getBackendToken()
  if (!token) {
    return NextResponse.json({ error: "no token" }, { status: 401 })
  }
  return NextResponse.json({ token })
}
