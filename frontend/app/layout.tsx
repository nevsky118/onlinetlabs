import type { Metadata } from "next"
import { ThemeProvider } from "@/components/theme-provider"
import { siteConfig } from "@/lib/config"
import { fontVariables } from "@/lib/fonts"
import { cn } from "@/lib/utils"

import "@/styles/globals.css"

import { Inter } from "next/font/google"
import { NuqsAdapter } from "nuqs/adapters/next/app"
import { AnalyticsProvider } from "@/components/analytics-provider"
import { LayoutProvider } from "@/hooks/use-layout"
import { Toaster } from "@/ui/sonner"
import { TooltipProvider } from "@/ui/tooltip"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })

export const metadata: Metadata = {
  title: {
    default: siteConfig.name,
    template: `%s - ${siteConfig.name}`,
  },
  // metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL!),
  description: siteConfig.description,
  // openGraph: {
  //   type: "website",
  //   locale: "en_US",
  //   url: process.env.NEXT_PUBLIC_APP_URL!,
  //   title: siteConfig.name,
  //   description: siteConfig.description,
  //   siteName: siteConfig.name,
  //   images: [
  //     {
  //       url: `${process.env.NEXT_PUBLIC_APP_URL}/opengraph-image.png`,
  //       width: 1200,
  //       height: 630,
  //       alt: siteConfig.name,
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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn("font-sans", inter.variable)}
    >
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
      </body>
    </html>
  )
}
