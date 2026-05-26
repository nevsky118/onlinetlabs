import Link from "next/link"

export default function Unauthorized() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">Требуется вход</h1>
      <p className="text-muted-foreground">
        Войдите, чтобы открыть эту страницу.
      </p>
      <Link
        href="/sign-in"
        className="bg-primary text-primary-foreground rounded-none px-4 py-2 text-sm font-medium"
      >
        Войти
      </Link>
    </div>
  )
}
