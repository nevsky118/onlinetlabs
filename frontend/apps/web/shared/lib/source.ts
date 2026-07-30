import { defineI18n } from "fumadocs-core/i18n"
import { loader } from "fumadocs-core/source"
import { course as courseSource, labs as labsSource } from "../../.source"

export const i18n = defineI18n({
  languages: ["ru", "en"],
  defaultLanguage: "ru", // content language and fallback source, not next-intl defaultLocale
  fallbackLanguage: "ru", // missing translation falls back to ru instead of 404
  hideLocale: "never", // same as next-intl localePrefix "always"
  parser: "dot", // index.ru.mdx / index.en.mdx
})

export const course = loader({
  baseUrl: "/courses",
  source: courseSource.toFumadocsSource(),
  i18n,
})

export const labs = loader({
  baseUrl: "/labs",
  source: labsSource.toFumadocsSource(),
  i18n,
})

export type FumaDocsPageTree = typeof course.pageTree | typeof labs.pageTree
