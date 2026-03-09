"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useQueryState } from "nuqs"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { redirectParser } from "../lib/search-params"
import { Icons } from "@/components/icons"
import { type LoginFormValues, loginSchema } from "@/entities/user"
import { validateRedirect } from "@/lib/redirect"
import { cn } from "@/lib/utils"
import { authClient } from "@/shared/auth/client"
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
      setServerError("GitHub sign-in failed. Try again.")
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
          setServerError(ctx.error.message ?? "Invalid email or password."),
      }
    )
  })

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>Sign In to Your Account</CardTitle>
          <CardDescription>
            Enter your email below to sign in to your account
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
                <FieldLabel htmlFor="password">Password</FieldLabel>
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
                Sign In
              </Button>
            </FieldGroup>
          </form>
          <div className="mt-6 flex flex-col gap-4">
            <div className="after:border-border relative text-center text-sm after:absolute after:inset-0 after:top-1/2 after:z-0 after:flex after:items-center after:border-t">
              <span className="bg-card text-muted-foreground relative z-10 px-2">
                or
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
              Sign In with GitHub
            </Button>
            <FieldDescription className="text-center">
              Don&apos;t have an account? <Link href="/sign-up">Sign Up</Link>
            </FieldDescription>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
