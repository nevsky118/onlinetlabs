import { AxiosError } from "axios"
import type { BetterAuthPlugin } from "better-auth"
import { APIError, createAuthEndpoint } from "better-auth/api"
import { setSessionCookie } from "better-auth/cookies"
import { z } from "zod"
import { type BackendUser, backendLogin, backendRegister } from "./api"

function toAuthUser(backendUser: {
  id: string
  email: string
  name?: string | null
  image?: string | null
}) {
  const now = new Date()
  return {
    id: backendUser.id,
    name: backendUser.name ?? "",
    email: backendUser.email,
    emailVerified: true,
    image: backendUser.image ?? null,
    createdAt: now,
    updatedAt: now,
  }
}

export const credentialAuthPlugin = () => {
  return {
    id: "credential-auth",
    endpoints: {
      signInCredential: createAuthEndpoint(
        "/sign-in/credential",
        {
          method: "POST",
          body: z.object({
            email: z.string().email(),
            password: z.string().min(8),
          }),
        },
        async (ctx) => {
          let backendUser: BackendUser
          try {
            backendUser = await backendLogin(ctx.body.email, ctx.body.password)
          } catch {
            throw new APIError("UNAUTHORIZED", {
              message: "Invalid email or password",
            })
          }

          const user = toAuthUser(backendUser)
          const session = await ctx.context.internalAdapter.createSession(
            user.id,
            false
          )

          if (!session) {
            throw new APIError("INTERNAL_SERVER_ERROR", {
              message: "Failed to create session",
            })
          }

          await setSessionCookie(ctx, { session, user })
          return ctx.json({ user, session })
        }
      ),
      signUpCredential: createAuthEndpoint(
        "/sign-up/credential",
        {
          method: "POST",
          body: z.object({
            name: z.string().optional(),
            email: z.string().email(),
            password: z.string().min(8),
          }),
        },
        async (ctx) => {
          let backendUser: BackendUser
          try {
            backendUser = await backendRegister(
              ctx.body.email,
              ctx.body.password,
              ctx.body.name
            )
          } catch (error) {
            const detail =
              error instanceof AxiosError
                ? error.response?.data?.detail
                : undefined
            throw new APIError("BAD_REQUEST", {
              message: detail ?? "Registration failed",
            })
          }

          const user = toAuthUser(backendUser)
          const session = await ctx.context.internalAdapter.createSession(
            user.id,
            false
          )

          if (!session) {
            throw new APIError("INTERNAL_SERVER_ERROR", {
              message: "Failed to create session",
            })
          }

          await setSessionCookie(ctx, { session, user })
          return ctx.json({ user, session })
        }
      ),
    },
  } satisfies BetterAuthPlugin
}
