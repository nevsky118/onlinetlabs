import { ThemeProvider } from "@repo/design-system/components/theme-provider"
import { fontVariables } from "@repo/design-system/lib/fonts"
import { cn } from "@repo/design-system/lib/utils"
import { pickMessages } from "@repo/i18n/messages"
import { routing } from "@repo/i18n/routing"
import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { hasLocale, NextIntlClientProvider } from "next-intl"
import { getTranslations, setRequestLocale } from "next-intl/server"

import "@repo/design-system/styles/globals.css"
// web renders MDX (courses/labs) through rehype-pretty-code, which needs docs.css
import "@repo/design-system/styles/docs.css"

import { LayoutProvider } from "@repo/design-system/hooks/use-layout"
import { Toaster } from "@repo/design-system/ui/sonner"
import { TooltipProvider } from "@repo/design-system/ui/tooltip"
import { AnalyticsProvider } from "@/app-components/analytics-provider"
import { SiteFooter } from "@/app-components/site-footer"
import { SiteHeader } from "@/app-components/site-header"
import { course, labs } from "@/lib/source"
import { webUrl } from "@/lib/urls"

const webNamespaces = ["shared", "web"]

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }))
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  setRequestLocale(locale)
  const t = await getTranslations("web.site")

  return {
    title: {
      default: t("name"),
      template: `%s - ${t("name")}`,
    },
    metadataBase: new URL(webUrl),
    description: t("description"),
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
  // Required to keep the route statically rendered
  setRequestLocale(locale)
  const t = await getTranslations("web.searchTree")

  const coursesPageTree = course.getPageTree(locale)
  const labsPageTree = labs.getPageTree(locale)
  // Synthetic tree for CommandMenu, courses and labs in one list
  const searchTree = {
    ...coursesPageTree,
    children: [
      {
        type: "folder" as const,
        $id: "courses",
        name: t("coursesGroup"),
        children: coursesPageTree.children,
      },
      {
        type: "folder" as const,
        $id: "labs",
        name: t("labsGroup"),
        children: labsPageTree.children,
      },
    ],
  } as typeof coursesPageTree

  return (
    <html lang={locale} suppressHydrationWarning className="font-sans">
      <head>
        <script
          // biome-ignore lint: security/no-dangerously-set-inner-html
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
          "text-foreground group/body overscroll-none font-sans antialiased [--footer-height:calc(var(--spacing)*14)] [--header-height:calc(var(--spacing)*14)] xl:[--footer-height:calc(var(--spacing)*24)]",
          fontVariables
        )}
      >
        <NextIntlClientProvider
          messages={await pickMessages(locale, webNamespaces)}
        >
          <AnalyticsProvider>
            <ThemeProvider>
              <LayoutProvider>
                <TooltipProvider>
                  <div
                    data-slot="layout"
                    className="bg-background relative z-10 flex min-h-svh flex-col"
                  >
                    <SiteHeader
                      searchTree={searchTree}
                      navTree={coursesPageTree}
                    />
                    <main className="flex flex-1 flex-col">{children}</main>
                    <SiteFooter locale={locale} />
                  </div>
                </TooltipProvider>
                <Toaster position="bottom-right" />
              </LayoutProvider>
            </ThemeProvider>
          </AnalyticsProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
