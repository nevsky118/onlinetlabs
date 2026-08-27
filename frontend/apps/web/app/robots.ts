import type { MetadataRoute } from "next"
import { webUrl } from "@/lib/urls"

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/"],
    },
    sitemap: `${webUrl}/sitemap.xml`,
  }
}
