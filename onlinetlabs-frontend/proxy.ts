import type { NextRequest } from "next/server"
import { NextResponse } from "next/server"

export function proxy(_request: NextRequest) {
  return NextResponse.next()
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|sign-in|sign-up).*)",
  ],
}
