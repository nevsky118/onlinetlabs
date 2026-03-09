import { SiteFooter } from "@/widgets/site-footer"
import { SiteHeader } from "@/widgets/site-header"

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
