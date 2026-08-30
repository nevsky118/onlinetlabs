"use client"

import { defaultRedirect, validateRedirect } from "@/lib/redirect"
import { zodResolver } from "@hookform/resolvers/zod"
import { authClient } from "@repo/auth/client"
import { Icons } from "@repo/design-system/components/icons"
import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@repo/design-system/ui/card"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@repo/design-system/ui/field"
import { Input } from "@repo/design-system/ui/input"
import { Spinner } from "@repo/design-system/ui/spinner"
import { Link } from "@repo/i18n/navigation"
import { useLocale, useTranslations } from "next-intl"
import { useRouter } from "next/navigation"
import { useQueryState } from "nuqs"
import { useMemo, useState } from "react"
import { useForm } from "react-hook-form"
import { getLoginSchema, type LoginFormValues } from "../lib/schemas"
import { redirectParser } from "../search-params"

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const t = useTranslations("dashboard.auth.loginForm")
  const schemaT = useTranslations("dashboard.auth.schemas")
  const locale = useLocale()
  const router = useRouter()
  const [redirect] = useQueryState("redirect", redirectParser)
  const [serverError, setServerError] = useState<string>()
  const [isGithubLoading, setIsGithubLoading] = useState(false)

  const onGithubSignIn = async () => {
    setIsGithubLoading(true)
    try {
      await authClient.signIn.social({
        provider: "github",
        callbackURL: validateRedirect(redirect, defaultRedirect(locale)),
      })
    } catch {
      setServerError(t("githubSignInError"))
      setIsGithubLoading(false)
    }
  }

  const loginSchema = useMemo(() => getLoginSchema(schemaT), [schemaT])

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
        onSuccess: () =>
          router.push(validateRedirect(redirect, defaultRedirect(locale))),
        onError: (ctx) =>
          setServerError(ctx.error.message ?? t("invalidCredentials")),
      }
    )
  })

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>{t("title")}</CardTitle>
          <CardDescription>{t("description")}</CardDescription>
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
                <FieldLabel htmlFor="password">{t("password")}</FieldLabel>
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
                {t("submit")}
              </Button>
            </FieldGroup>
          </form>
          <div className="mt-6 flex flex-col gap-4">
            <div className="relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t after:border-border">
              <span className="relative z-10 bg-card px-2 text-muted-foreground">
                {t("orDivider")}
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
              {t("githubButton")}
            </Button>
            <FieldDescription className="text-center">
              {t.rich("noAccount", {
                link: (chunks) => <Link href="/sign-up">{chunks}</Link>,
              })}
            </FieldDescription>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
