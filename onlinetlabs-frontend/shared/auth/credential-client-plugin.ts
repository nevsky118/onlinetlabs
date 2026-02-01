import type { BetterAuthClientPlugin } from "better-auth/client"
import type { credentialAuthPlugin } from "./credential-plugin"

export const credentialAuthClientPlugin = {
  id: "credential-auth",
  $InferServerPlugin: {} as ReturnType<typeof credentialAuthPlugin>,
} satisfies BetterAuthClientPlugin
