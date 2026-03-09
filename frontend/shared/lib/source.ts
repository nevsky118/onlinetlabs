import { loader } from "fumadocs-core/source"
import { course as courseSource, labs as labsSource } from "@/.source"

export const course = loader({
  baseUrl: "/courses",
  source: courseSource.toFumadocsSource(),
})

export const labs = loader({
  baseUrl: "/labs",
  source: labsSource.toFumadocsSource(),
})

export type FumaDocsPageTree = typeof course.pageTree | typeof labs.pageTree
