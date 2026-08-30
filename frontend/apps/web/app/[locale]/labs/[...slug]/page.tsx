import { absoluteUrl } from "@/lib/absolute-url"
import { siteConfig } from "@/lib/config"
import { ogImagePath, ogSize } from "@/lib/og-image"
import { i18n, labs } from "@/lib/source"
import { getMdxComponents } from "@/mdx-components"
import { DocsTableOfContents } from "@repo/design-system/components/docs-toc"
import { Badge } from "@repo/design-system/ui/badge"
import { Button } from "@repo/design-system/ui/button"
import { routing } from "@repo/i18n/routing"
import fm from "front-matter"
import { findNeighbour } from "fumadocs-core/page-tree"
import { ArrowLeftIcon, ArrowRightIcon, ArrowUpRightIcon } from "lucide-react"
import { getTranslations, setRequestLocale } from "next-intl/server"
import Link from "next/link"
import { notFound } from "next/navigation"
import { z } from "zod"
import { LaunchLink } from "./_components/launch-link"

export const dynamic = "force-static"
export const revalidate = false
export const dynamicParams = false

export function generateStaticParams() {
  return [
    ...i18n.languages.map((locale) => ({ slug: [], locale })),
    ...labs.generateParams("slug", "locale"),
  ]
}

export async function generateMetadata(props: {
  params: Promise<{ slug?: string[]; locale: string }>
}) {
  const params = await props.params

  if (!params.slug || params.slug.length === 0) {
    setRequestLocale(params.locale)
    const t = await getTranslations("web.labs")
    return {
      title: t("title"),
      description: t("description"),
    }
  }

  const page = labs.getPage(params.slug, params.locale)

  if (!page) {
    notFound()
  }

  const doc = page.data

  if (!doc.title || !doc.description) {
    notFound()
  }

  const ogImage = {
    url: absoluteUrl(ogImagePath(params.locale, "labs", params.slug)),
    width: ogSize.width,
    height: ogSize.height,
    alt: doc.title,
  }

  return {
    title: doc.title,
    description: doc.description,
    alternates: {
      canonical: absoluteUrl(page.url),
      languages: Object.fromEntries(
        routing.locales.map((alternate) => [
          alternate,
          absoluteUrl(labs.getPage(params.slug, alternate)?.url ?? page.url),
        ])
      ),
    },
    openGraph: {
      title: doc.title,
      description: doc.description,
      type: "article",
      url: absoluteUrl(page.url),
      images: [ogImage],
    },
    twitter: {
      card: "summary_large_image",
      title: doc.title,
      description: doc.description,
      images: [ogImage],
      creator: siteConfig.author,
    },
  }
}

export default async function Page(props: {
  params: Promise<{ slug?: string[]; locale: string }>
}) {
  const params = await props.params
  setRequestLocale(params.locale)
  const [t, tMdx] = await Promise.all([
    getTranslations("web.labsDoc"),
    getTranslations("web.mdx"),
  ])

  if (!params.slug || params.slug.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <p className="text-muted-foreground">{t("emptyList")}</p>
      </div>
    )
  }

  const page = labs.getPage(params.slug, params.locale)
  if (!page) {
    notFound()
  }

  const doc = page.data
  const MDX = doc.body
  const neighbours = findNeighbour(labs.getPageTree(params.locale), page.url)

  const raw = await page.data.getText("raw")
  const { attributes } = fm(raw)
  const { links } = z
    .object({
      links: z
        .object({
          doc: z.string().optional(),
          api: z.string().optional(),
        })
        .optional(),
    })
    .parse(attributes)

  return (
    <div
      data-slot="docs"
      className="flex items-stretch text-[1.05rem] sm:text-[15px] xl:w-full"
    >
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="h-(--top-spacing) shrink-0" />
        <div className="mx-auto flex w-full max-w-2xl min-w-0 flex-1 flex-col gap-8 px-4 py-6 text-neutral-800 md:px-0 lg:py-8 dark:text-neutral-300">
          <div className="flex flex-col gap-2">
            <div className="flex flex-col gap-2">
              <div className="flex items-start justify-between">
                <h1 className="scroll-m-20 text-4xl font-semibold tracking-tight sm:text-3xl xl:text-4xl">
                  {doc.title}
                </h1>
                <div className="docs-nav fixed inset-x-0 bottom-0 isolate z-50 flex items-center gap-2 border-t border-border/50 bg-background/80 px-6 py-4 backdrop-blur-sm sm:static sm:z-0 sm:border-t-0 sm:bg-transparent sm:px-0 sm:pt-1.5 sm:backdrop-blur-none">
                  {neighbours.previous && (
                    <Button
                      nativeButton={false}
                      variant="secondary"
                      size="icon"
                      className="extend-touch-target ml-auto size-8 shadow-none md:size-7"
                      render={<Link href={neighbours.previous.url} />}
                    >
                      <ArrowLeftIcon />
                      <span className="sr-only">{t("previous")}</span>
                    </Button>
                  )}
                  {neighbours.next && (
                    <Button
                      nativeButton={false}
                      variant="secondary"
                      size="icon"
                      className="extend-touch-target size-8 shadow-none md:size-7"
                      render={<Link href={neighbours.next.url} />}
                    >
                      <span className="sr-only">{t("next")}</span>
                      <ArrowRightIcon />
                    </Button>
                  )}
                </div>
              </div>
              {doc.description && (
                <p className="text-[1.05rem] text-balance text-muted-foreground sm:text-base">
                  {doc.description}
                </p>
              )}
              {doc.launchable !== false && (
                <div className="pt-4">
                  <LaunchLink labSlug={params.slug.join("/")} />
                </div>
              )}
            </div>
            {links ? (
              <div className="flex items-center gap-2 pt-4">
                {links?.doc && (
                  <Badge
                    variant="secondary"
                    className="rounded-none"
                    render={
                      // oxlint-disable-next-line jsx-a11y/anchor-has-content -- link text comes from the Base UI render slot
                      <a href={links.doc} target="_blank" rel="noreferrer" />
                    }
                  >
                    {t("docsLink")} <ArrowUpRightIcon />
                  </Badge>
                )}
                {links?.api && (
                  <Badge
                    variant="secondary"
                    className="rounded-none"
                    render={
                      // oxlint-disable-next-line jsx-a11y/anchor-has-content -- link text comes from the Base UI render slot
                      <a href={links.api} target="_blank" rel="noreferrer" />
                    }
                  >
                    API <ArrowUpRightIcon />
                  </Badge>
                )}
              </div>
            ) : null}
          </div>
          <div className="w-full flex-1 *:data-[slot=alert]:first:mt-0">
            <MDX
              components={getMdxComponents({
                locale: params.locale,
                labelCopy: tMdx("copy"),
                labelCopied: tMdx("copied"),
                labelCollapse: tMdx("collapse"),
                labelExpand: tMdx("expand"),
              })}
            />
          </div>
        </div>
        <div className="mx-auto hidden h-16 w-full max-w-2xl items-center gap-2 px-4 sm:flex md:px-0">
          {neighbours.previous && (
            <Button
              nativeButton={false}
              variant="secondary"
              size="sm"
              className="shadow-none"
              render={<Link href={neighbours.previous.url} />}
            >
              <ArrowLeftIcon /> {neighbours.previous.name}
            </Button>
          )}
          {neighbours.next && (
            <Button
              nativeButton={false}
              variant="secondary"
              size="sm"
              className="ml-auto shadow-none"
              render={<Link href={neighbours.next.url} />}
            >
              {neighbours.next.name} <ArrowRightIcon />
            </Button>
          )}
        </div>
      </div>
      <div className="sticky top-[calc(var(--header-height)+1px)] z-30 ml-auto hidden h-[calc(100svh-var(--footer-height)+2rem)] w-72 flex-col gap-4 overflow-hidden overscroll-none pb-8 xl:flex">
        <div className="h-(--top-spacing) shrink-0" />
        {doc.toc?.length ? (
          <div className="no-scrollbar overflow-y-auto px-8">
            <DocsTableOfContents toc={doc.toc} />
          </div>
        ) : null}
      </div>
    </div>
  )
}
