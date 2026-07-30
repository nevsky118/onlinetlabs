import { z } from "zod"

/** Built per call because the messages come from the active translations. */
export function getLoginSchema(t: (key: string) => string) {
  return z.object({
    email: z.string().email(t("invalidEmail")),
    password: z.string().min(1, t("passwordRequired")),
  })
}

export type LoginFormValues = z.infer<ReturnType<typeof getLoginSchema>>

export function getRegisterSchema(t: (key: string) => string) {
  return z.object({
    name: z.string().optional(),
    email: z.string().email(t("invalidEmail")),
    password: z.string().min(8, t("passwordMinLength")),
  })
}

export type RegisterFormValues = z.infer<ReturnType<typeof getRegisterSchema>>
