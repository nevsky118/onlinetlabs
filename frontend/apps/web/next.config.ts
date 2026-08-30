import { baseConfig } from "@repo/next-config"
import { createMDX } from "fumadocs-mdx/next"
import createNextIntlPlugin from "next-intl/plugin"
import type { NextConfig } from "next"

const withMDX = createMDX()
const withNextIntl = createNextIntlPlugin("../../packages/i18n/request.ts")

// transpilePackages is web-specific and not part of baseConfig
const nextConfig: NextConfig = {
  ...baseConfig,
  transpilePackages: ["@repo/design-system"],
}

export default withNextIntl(withMDX(nextConfig))
