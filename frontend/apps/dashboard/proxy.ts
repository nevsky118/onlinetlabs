import { routing } from "@repo/i18n/routing"
import createMiddleware from "next-intl/middleware"

export default createMiddleware(routing)

export const config = {
  // Skip api, Next static assets and any path with a file extension
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
}
