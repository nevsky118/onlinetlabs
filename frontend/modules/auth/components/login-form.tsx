"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useQueryState } from "nuqs"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { type LoginFormValues, loginSchema } from "../lib/schemas"
import { redirectParser } from "../search-params"
import { authClient } from "@/auth/client"
import { Icons } from "@/components/icons"
import { validateRedirect } from "@/lib/redirect"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/ui/card"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/ui/field"
import { Input } from "@/ui/input"
import { Spinner } from "@/ui/spinner"

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const router = useRouter()
  const [redirect] = useQueryState("redirect", redirectParser)
  const [serverError, setServerError] = useState<string>()
  const [isGithubLoading, setIsGithubLoading] = useState(false)

  const onGithubSignIn = async () => {
    setIsGithubLoading(true)
    try {
      await authClient.signIn.social({
        provider: "github",
        callbackURL: validateRedirect(redirect),
      })
    } catch {
      setServerError("Не удалось войти через GitHub. Попробуйте снова.")
      setIsGithubLoading(false)
    }
  }

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = handleSubmit(async (data) => {
    setServerError(undefined)
    await authClient.signIn.credential(
      { email: data.email, password: data.password },
      {
        onSuccess: () => router.push(validateRedirect(redirect)),
        onError: (ctx) =>
          setServerError(ctx.error.message ?? "Неверный email или пароль."),
      }
    )
  })

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>Вход в аккаунт</CardTitle>
          <CardDescription>
            Введите email, чтобы войти в аккаунт
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit}>
            <FieldGroup>
              {serverError && (
                <FieldError aria-live="polite">{serverError}</FieldError>
              )}
              <Field>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  spellCheck={false}
                  placeholder="m@example.com"
                  {...register("email")}
                />
                {errors.email && (
                  <FieldError>{errors.email.message}</FieldError>
                )}
              </Field>
              <Field>
                <FieldLabel htmlFor="password">Пароль</FieldLabel>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  {...register("password")}
                />
                {errors.password && (
                  <FieldError>{errors.password.message}</FieldError>
                )}
              </Field>
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting && <Spinner />}
                Войти
              </Button>
            </FieldGroup>
          </form>
          <div className="mt-6 flex flex-col gap-4">
            <div className="after:border-border relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t">
              <span className="bg-card text-muted-foreground relative z-10 px-2">
                или
              </span>
            </div>
            <Button
              variant="outline"
              className="w-full"
              type="button"
              onClick={onGithubSignIn}
              disabled={isGithubLoading}
            >
              {isGithubLoading ? (
                <Spinner />
              ) : (
                <Icons.gitHub aria-hidden="true" />
              )}
              Войти через GitHub
            </Button>
            <FieldDescription className="text-center">
              Нет аккаунта? <Link href="/sign-up">Зарегистрироваться</Link>
            </FieldDescription>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
