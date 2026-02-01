import { toNextJsHandler } from "better-auth/next-js"
import { auth } from "@/shared/auth"

export const { GET, POST } = toNextJsHandler(auth)
