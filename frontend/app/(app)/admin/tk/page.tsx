import type { Metadata } from "next"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { TkView } from "@/modules/admin/views/tk-view"

const title = "Закон T_k"
const description =
  "Чувствительность порога вмешательства к стоимости застревания"

export const metadata: Metadata = { title: "Закон T_k — Администратор" }

export default function AdminTkPage() {
  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <TkView />
        </div>
      </div>
    </div>
  )
}
