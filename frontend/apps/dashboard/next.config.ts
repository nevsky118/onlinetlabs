import { baseConfig } from "@repo/next-config"
import createNextIntlPlugin from "next-intl/plugin"
import type { NextConfig } from "next"

const withNextIntl = createNextIntlPlugin("../../packages/i18n/request.ts")

// transpilePackages is dashboard-specific and stays out of baseConfig
const nextConfig: NextConfig = {
  ...baseConfig,
  transpilePackages: ["@repo/design-system"],
}

export default withNextIntl(nextConfig)
