import { baseConfig } from "@repo/next-config"
import { createMDX } from "fumadocs-mdx/next"
import type { NextConfig } from "next"
import createNextIntlPlugin from "next-intl/plugin"

const withMDX = createMDX()
const withNextIntl = createNextIntlPlugin("../../packages/i18n/request.ts")

// transpilePackages is web-specific and not part of baseConfig
const nextConfig: NextConfig = {
  ...baseConfig,
  transpilePackages: ["@repo/design-system"],
}

export default withNextIntl(withMDX(nextConfig))
