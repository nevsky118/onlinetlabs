import { adminClient } from "better-auth/client/plugins"
import { createAuthClient } from "better-auth/react"
import { credentialAuthClientPlugin } from "./credential-client-plugin"
import { ac, roles } from "./permissions"

export const authClient = createAuthClient({
  // В браузере берём текущий origin, чтобы вход работал с любого хоста
  // (localhost, 127.0.0.1, IP в сети). NEXT_PUBLIC_APP_URL остаётся фолбэком для SSR.
  baseURL:
    typeof window !== "undefined"
      ? window.location.origin
      : process.env.NEXT_PUBLIC_APP_URL,
  plugins: [credentialAuthClientPlugin, adminClient({ ac, roles })],
})
