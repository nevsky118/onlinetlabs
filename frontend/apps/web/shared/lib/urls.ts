// Single read point for origin env vars
// Fallbacks are required so the build does not bake "undefined" into static pages
export const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"
export const webUrl = process.env.NEXT_PUBLIC_WEB_URL ?? "http://localhost:3001"
