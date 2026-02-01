import { betterAuth } from "better-auth"
import { nextCookies } from "better-auth/next-js"
import { admin } from "better-auth/plugins"
import { backendUpsertGithubUser } from "./api"
import { credentialAuthPlugin } from "./credential-plugin"
import { ac, roles } from "./permissions"

export const auth = betterAuth({
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID ?? "",
      clientSecret: process.env.GITHUB_CLIENT_SECRET ?? "",
    },
  },
  plugins: [
    credentialAuthPlugin(),
    admin({ ac, roles, defaultRole: "student" }),
    nextCookies(),
  ],
  session: {
    cookieCache: {
      enabled: true,
      maxAge: 7 * 24 * 60 * 60,
      strategy: "jwt",
      refreshCache: true,
    },
  },
  account: {
    storeStateStrategy: "cookie",
    storeAccountCookie: true,
  },
  databaseHooks: {
    user: {
      create: {
        after: async (user) => {
          try {
            await backendUpsertGithubUser({
              email: user.email,
              name: user.name,
              image: user.image,
              provider_account_id: user.id,
            })
          } catch {
            console.error("[auth] Failed to sync GitHub user to backend")
          }
        },
      },
    },
  },
})
