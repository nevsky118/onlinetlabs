import { adminClient } from "better-auth/client/plugins"
import { createAuthClient } from "better-auth/react"
import { credentialAuthClientPlugin } from "./credential-client-plugin"
import { ac, roles } from "./permissions"

export const authClient = createAuthClient({
  // Explicit origin that mounts /api/auth/*, the dashboard.
  // Falls back to NEXT_PUBLIC_APP_URL while NEXT_PUBLIC_AUTH_URL is unset in local development.
  baseURL: process.env.NEXT_PUBLIC_AUTH_URL ?? process.env.NEXT_PUBLIC_APP_URL,
  // web calls this cross-origin, where the session cookie needs credentials included.
  fetchOptions: { credentials: "include" },
  plugins: [credentialAuthClientPlugin, adminClient({ ac, roles })],
})
