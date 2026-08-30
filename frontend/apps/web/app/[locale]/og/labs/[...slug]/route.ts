import { renderOgImage } from "@/lib/og-image"
import { labs } from "@/lib/source"
import { getTranslations } from "next-intl/server"

export const dynamic = "force-static"
export const dynamicParams = false

export function generateStaticParams() {
  return labs.generateParams("slug", "locale")
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ slug: string[]; locale: string }> }
) {
  const { slug, locale } = await params
  const page = labs.getPage(slug, locale)
  if (!page) return new Response(null, { status: 404 })

  const t = await getTranslations({ locale, namespace: "web.labs" })

  return renderOgImage({
    eyebrow: t("title"),
    title: page.data.title,
    description: page.data.description,
  })
}
