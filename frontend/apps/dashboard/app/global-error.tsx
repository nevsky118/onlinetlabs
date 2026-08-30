"use client"

import "@repo/design-system/styles/globals.css"
import { useIsHydrated } from "@repo/design-system/hooks/use-is-hydrated"

// The root layout is what failed, so NextIntlClientProvider went down with it
// and the message catalog is out of reach. localePrefix is "always", so the
// locale is still readable from the URL and these few strings live here.
const COPY = {
  en: {
    heading: "Something went wrong",
    description: "The application failed to load.",
    retry: "Try again",
  },
  ru: {
    heading: "Что-то пошло не так",
    description: "Приложение не удалось загрузить.",
    retry: "Повторить",
  },
} as const

type FallbackLocale = keyof typeof COPY

const DEFAULT_LOCALE: FallbackLocale = "en"

function readLocaleFromPath(): FallbackLocale {
  const segment = window.location.pathname.split("/")[1]
  return segment in COPY ? (segment as FallbackLocale) : DEFAULT_LOCALE
}

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  // The URL is only readable once the document exists. When this screen is
  // rendered straight on the client there is no hydration pass, so the right
  // locale is picked on the very first paint.
  const locale = useIsHydrated() ? readLocaleFromPath() : DEFAULT_LOCALE
  const copy = COPY[locale]

  return (
    <html lang={locale}>
      <body className="flex min-h-svh flex-col items-center justify-center gap-4 bg-background text-foreground antialiased">
        <h1 className="text-2xl font-bold">{copy.heading}</h1>
        <p className="text-muted-foreground">{copy.description}</p>
        <button
          type="button"
          onClick={reset}
          className="rounded-none bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          {copy.retry}
        </button>
      </body>
    </html>
  )
}
