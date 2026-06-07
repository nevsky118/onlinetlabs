import type { Metadata } from "next"
import {
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/page-header"
import { HydrateClient, prefetchQuery } from "@/lib/query-hydration"
import { SessionsView, sessionsListQuery } from "@/modules/session/server"

const title = "Мои лабы"
const description = "Запущенные и недавние учебные сессии"

export const metadata: Metadata = { title, description }

export default async function SessionsPage() {
  await prefetchQuery(sessionsListQuery())

  return (
    <div className="flex flex-1 flex-col">
      <PageHeader>
        <PageHeaderHeading>{title}</PageHeaderHeading>
        <PageHeaderDescription>{description}</PageHeaderDescription>
      </PageHeader>
      <div className="container-wrapper section-soft flex-1 pb-6">
        <div className="container">
          <HydrateClient>
            <SessionsView />
          </HydrateClient>
        </div>
      </div>
    </div>
  )
}
