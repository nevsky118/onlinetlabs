import type { Metadata } from "next"
import { PageHeader, PageHeaderHeading } from "@/components/page-header"
import { OverviewView } from "@/modules/admin/views/overview-view"

export const metadata: Metadata = { title: "Обзор — Администратор" }

export default function AdminOverviewPage() {
  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>Обзор</PageHeaderHeading>
      </PageHeader>
      <div className="p-4 md:p-6">
        <OverviewView />
      </div>
    </div>
  )
}
