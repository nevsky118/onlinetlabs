import type { Metadata } from "next"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { OverviewView } from "@/modules/admin/views/overview-view"

const title = "Обзор"
const description = "Сводка ключевых метрик контура управления"

export const metadata: Metadata = { title: "Обзор — Администратор" }

export default function AdminOverviewPage() {
  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <OverviewView />
        </div>
      </div>
    </div>
  )
}
