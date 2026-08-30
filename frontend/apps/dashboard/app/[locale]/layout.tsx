import { AnalyticsProvider } from "@/app-components/analytics-provider"
import { QueryProvider } from "@/app-components/query-provider"
import { rootMessages } from "@/lib/messages"
import { ThemeProvider } from "@repo/design-system/components/theme-provider"
import { LayoutProvider } from "@repo/design-system/hooks/use-layout"
import { fontVariables } from "@repo/design-system/lib/fonts"
import { cn } from "@repo/design-system/lib/utils"
import { Toaster } from "@repo/design-system/ui/sonner"
import "@repo/design-system/styles/globals.css"
import { TooltipProvider } from "@repo/design-system/ui/tooltip"
import { routing } from "@repo/i18n/routing"
import { hasLocale, NextIntlClientProvider } from "next-intl"
import { getTranslations, setRequestLocale } from "next-intl/server"
import { notFound } from "next/navigation"
import { NuqsAdapter } from "nuqs/adapters/next/app"
import type { Metadata } from "next"

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }))
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: "dashboard.app.site" })

  return {
    title: {
      default: t("name"),
      template: `%s - ${t("name")}`,
    },
    metadataBase: new URL(
      process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"
    ),
    description: t("description"),
    // openGraph: {
    //   type: "website",
    //   locale: "en_US",
    //   url: process.env.NEXT_PUBLIC_APP_URL!,
    //   title: t("name"),
    //   description: t("description"),
    //   siteName: t("name"),
    //   images: [
    //     {
    //       url: `${process.env.NEXT_PUBLIC_APP_URL}/opengraph-image.png`,
    //       width: 1200,
    //       height: 630,
    //       alt: t("name"),
    //     },
    //   ],
    // },
    // icons: {
    //   icon: "/favicon.ico",
    //   shortcut: "/favicon-16x16.png",
    //   apple: "/apple-touch-icon.png",
    // },
    // manifest: `${siteConfig.url}/site.webmanifest`,
  }
}

export default async function RootLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode
  params: Promise<{ locale: string }>
}>) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  // Without this the route becomes dynamic
  setRequestLocale(locale)

  return (
    <html lang={locale} suppressHydrationWarning className="font-sans">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                if (localStorage.layout) {
                  document.documentElement.classList.add('layout-' + localStorage.layout)
                }
              } catch (_) {}
            `,
          }}
        />
      </head>
      <body
        className={cn(
          "group/body overscroll-none font-sans text-foreground antialiased [--footer-height:calc(var(--spacing)*14)] [--header-height:calc(var(--spacing)*14)] xl:[--footer-height:calc(var(--spacing)*24)]",
          fontVariables
        )}
      >
        <NextIntlClientProvider messages={await rootMessages(locale)}>
          <QueryProvider>
            <AnalyticsProvider>
              <ThemeProvider>
                <NuqsAdapter>
                  <LayoutProvider>
                    <TooltipProvider>{children}</TooltipProvider>
                    <Toaster position="bottom-right" />
                  </LayoutProvider>
                </NuqsAdapter>
              </ThemeProvider>
            </AnalyticsProvider>
          </QueryProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
