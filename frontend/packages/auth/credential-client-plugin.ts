import type { credentialAuthPlugin } from "./credential-plugin"
import type { BetterAuthClientPlugin } from "better-auth/client"

export const credentialAuthClientPlugin = {
  id: "credential-auth",
  $InferServerPlugin: {} as ReturnType<typeof credentialAuthPlugin>,
} satisfies BetterAuthClientPlugin
