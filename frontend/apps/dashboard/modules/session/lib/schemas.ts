import { z } from "zod"

export const launchSchema = z.object({
  labSlug: z.string().min(1),
})
