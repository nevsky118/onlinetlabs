import { SiteFooter } from "./_components/site-footer"
import { SiteHeader } from "./_components/site-header"

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div
      data-slot="layout"
      className="bg-background relative z-10 flex min-h-svh flex-col"
    >
      <SiteHeader />
      <main className="flex flex-1 flex-col">{children}</main>
      <SiteFooter />
    </div>
  )
}
