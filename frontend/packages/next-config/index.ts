import path from "node:path"
import type { NextConfig } from "next"

// Shared base for both apps. outputFileTracingRoot is required in the monorepo.
// Without it Next traces from apps/<name> and silently drops workspace packages.
export const baseConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  outputFileTracingRoot: path.join(import.meta.dirname, "../../"),
  experimental: { authInterrupts: true },
}
