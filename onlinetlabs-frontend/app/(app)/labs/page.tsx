import type { Metadata } from "next"
import { ContentCard } from "@/components/content-card"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { labs } from "@/lib/source"

const title = "Лабораторные работы"
const description = "Список доступных лабораторных работ."

export const dynamic = "force-static"
export const revalidate = false

export const metadata: Metadata = {
  title,
  description,
}

export default function LabsPage() {
  const pages = labs.getPages()

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {pages.map((page) => (
              <ContentCard
                key={page.url}
                href={page.url}
                title={page.data.title}
                description={page.data.description}
                tasks={page.data.tasks}
                difficulty={page.data.difficulty}
                tags={page.data.tags}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
