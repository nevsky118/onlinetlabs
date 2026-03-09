import Link from "next/link"

export default function Unauthorized() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">Sign in required</h1>
      <p className="text-muted-foreground">
        You need to sign in to access this page.
      </p>
      <Link
        href="/sign-in"
        className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium"
      >
        Sign in
      </Link>
    </div>
  )
}
