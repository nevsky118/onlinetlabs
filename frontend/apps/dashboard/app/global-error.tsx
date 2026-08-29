"use client"

import "@repo/design-system/styles/globals.css"

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html lang="en">
      <body className="bg-background text-foreground flex min-h-svh flex-col items-center justify-center gap-4 antialiased">
        <h1 className="text-2xl font-bold">Something went wrong</h1>
        <p className="text-muted-foreground">
          The application failed to load. Приложение не удалось загрузить.
        </p>
        <button
          type="button"
          onClick={reset}
          className="bg-primary text-primary-foreground rounded-none px-4 py-2 text-sm font-medium"
        >
          Try again / Повторить
        </button>
      </body>
    </html>
  )
}
