import Link from "next/link"

export default function Forbidden() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">Доступ запрещён</h1>
      <p className="text-muted-foreground">
        У вас нет доступа к этой странице.
      </p>
      <Link
        href="/"
        className="bg-primary text-primary-foreground rounded-none px-4 py-2 text-sm font-medium"
      >
        На главную
      </Link>
    </div>
  )
}
