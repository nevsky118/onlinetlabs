import { z } from "zod"

export const loginSchema = z.object({
  email: z.string().email("Некорректный email"),
  password: z.string().min(1, "Введите пароль"),
})

export type LoginFormValues = z.infer<typeof loginSchema>

export const registerSchema = z.object({
  name: z.string().optional(),
  email: z.string().email("Некорректный email"),
  password: z.string().min(8, "Минимум 8 символов"),
})

export type RegisterFormValues = z.infer<typeof registerSchema>
