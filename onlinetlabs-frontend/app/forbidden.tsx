import Link from "next/link"

export default function Forbidden() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">Access denied</h1>
      <p className="text-muted-foreground">
        You don&apos;t have permission to access this page.
      </p>
      <Link
        href="/"
        className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium"
      >
        Go home
      </Link>
    </div>
  )
}
