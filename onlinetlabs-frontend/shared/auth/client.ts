import { adminClient } from "better-auth/client/plugins"
import { createAuthClient } from "better-auth/react"
import { credentialAuthClientPlugin } from "./credential-client-plugin"
import { ac, roles } from "./permissions"

export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_APP_URL,
  plugins: [credentialAuthClientPlugin, adminClient({ ac, roles })],
})
