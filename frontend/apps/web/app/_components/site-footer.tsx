import { siteConfig } from "@/lib/config"
import { getTranslations } from "next-intl/server"

export async function SiteFooter() {
  const t = await getTranslations("web.footer")

  return (
    <footer className="group-has-data-[slot=designer]/body:hidden group-has-[.docs-nav]/body:pb-20 group-has-[.section-soft]/body:bg-surface/40 group-has-[.docs-nav]/body:sm:pb-0 dark:bg-transparent 3xl:fixed:bg-transparent">
      <div className="container-wrapper px-4 xl:px-6">
        <div className="flex h-(--footer-height) items-center justify-between">
          <div className="w-full px-1 text-center text-xs leading-loose text-muted-foreground sm:text-sm">
            {t("sourceCode")}{" "}
            <a
              href={siteConfig.links.github}
              target="_blank"
              rel="noreferrer"
              className="font-medium underline underline-offset-4"
            >
              GitHub
            </a>
            .
          </div>
        </div>
      </div>
    </footer>
  )
}
