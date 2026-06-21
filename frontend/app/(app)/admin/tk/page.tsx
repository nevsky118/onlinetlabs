import type { Metadata } from "next"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { TkView } from "@/modules/admin/views/tk-view"

export const metadata: Metadata = { title: "Закон T_k — Администратор" }

export default function AdminTkPage() {
  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>Закон T_k</PageHeaderHeading>
        <PageHeaderDescription>
          Чувствительность порога вмешательства к стоимости застревания
        </PageHeaderDescription>
      </PageHeader>
      <div className="p-4 md:p-6">
        <TkView />
      </div>
    </div>
  )
}
