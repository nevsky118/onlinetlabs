import { betterAuth } from "better-auth"
import { nextCookies } from "better-auth/next-js"
import { admin } from "better-auth/plugins"
import { backendUpsertGithubUser } from "./api"
import { credentialAuthPlugin } from "./credential-plugin"
import { ac, roles } from "./permissions"

export const auth = betterAuth({
  baseURL: process.env.BETTER_AUTH_URL,
  trustedOrigins: [
    process.env.NEXT_PUBLIC_WEB_URL!,
    process.env.NEXT_PUBLIC_APP_URL!,
  ],
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID ?? "",
      clientSecret: process.env.GITHUB_CLIENT_SECRET ?? "",
    },
  },
  advanced: {
    // Without an explicit domain better-auth uses the full baseURL host instead of the registrable root, so cookies never reach web.
    // Gated on COOKIE_DOMAIN rather than NODE_ENV, which Next inlines at build time. Empty locally, set in compose.yaml for prod.
    ...(process.env.COOKIE_DOMAIN && {
      crossSubDomainCookies: {
        enabled: true,
        domain: process.env.COOKIE_DOMAIN,
      },
    }),
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
          } catch (error) {
            // Not fatal: getBackendToken re-syncs on the first 401.
            console.error("[auth] backend user sync failed on create", error)
          }
        },
      },
    },
  },
})
