import { course, labs } from "@/lib/source"
import { webUrl } from "@/lib/urls"
import { routing } from "@repo/i18n/routing"
import type { MetadataRoute } from "next"

export default function sitemap(): MetadataRoute.Sitemap {
  const entries: MetadataRoute.Sitemap = []

  for (const locale of routing.locales) {
    entries.push({ url: `${webUrl}/${locale}` })
    entries.push({ url: `${webUrl}/${locale}/courses` })
    entries.push({ url: `${webUrl}/${locale}/labs` })
    // No footer link any more, so the sitemap is what keeps these reachable.
    entries.push({ url: `${webUrl}/${locale}/privacy` })
    entries.push({ url: `${webUrl}/${locale}/terms` })

    for (const page of course.getPages(locale)) {
      entries.push({
        url: `${webUrl}/${locale}/courses/${page.slugs.join("/")}`,
      })
    }
    for (const page of labs.getPages(locale)) {
      entries.push({ url: `${webUrl}/${locale}/labs/${page.slugs.join("/")}` })
    }
  }

  return entries
}
