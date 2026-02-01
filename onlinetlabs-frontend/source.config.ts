import {
  defineConfig,
  defineDocs,
  frontmatterSchema,
} from "fumadocs-mdx/config"
import rehypePrettyCode from "rehype-pretty-code"
import { z } from "zod"
import { transformers } from "@/lib/highlight-code"

export default defineConfig({
  mdxOptions: {
    rehypePlugins: (plugins) => {
      plugins.shift()
      plugins.push([
        // TODO: fix the type.
        // biome-ignore lint: @typescript-eslint/no-explicit-any
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
