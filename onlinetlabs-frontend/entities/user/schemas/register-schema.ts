import { z } from "zod"

export const registerSchema = z.object({
  name: z.string().optional(),
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "At least 8 characters"),
})

export type RegisterFormValues = z.infer<typeof registerSchema>
