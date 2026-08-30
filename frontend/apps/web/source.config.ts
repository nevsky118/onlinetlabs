import { transformers } from "@/lib/highlight-code"
import {
  defineConfig,
  defineDocs,
  frontmatterSchema,
} from "fumadocs-mdx/config"
// oxlint-disable-next-line import/no-named-as-default -- the plugin factory is the default export
import rehypePrettyCode from "rehype-pretty-code"
import { z } from "zod"

// This file may only export collections and a default. The loader() i18n config lives in shared/lib/source.ts

export default defineConfig({
  mdxOptions: {
    rehypePlugins: (plugins) => {
      plugins.shift()
      plugins.push([
        // TODO: fix the type.
        rehypePrettyCode as any,
        {
          theme: {
            dark: "github-dark",
            light: "github-light-default",
          },
          transformers,
        },
      ])

      return plugins
    },
  },
})

const contentSchema = frontmatterSchema.extend({
  title: z.string(),
  description: z.string(),
  tasks: z.number().optional(),
  difficulty: z.enum(["easy", "medium", "hard"]).optional(),
  duration: z.string().optional(),
  launchable: z.boolean().default(true),
  tags: z.array(z.string()).default([]),
})

export const course = defineDocs({
  dir: "content/courses",
  docs: {
    schema: contentSchema,
  },
})

export const labs = defineDocs({
  dir: "content/labs",
  docs: {
    schema: contentSchema,
  },
})
