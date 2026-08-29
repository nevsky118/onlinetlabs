import { pickMessages } from "@repo/i18n/messages"

const root = ["dashboard.app.error"]

const app = [
  ...root,
  "shared",
  "dashboard.app.commandMenu",
  "dashboard.app.mobileNav",
  "dashboard.app.siteConfig",
  "dashboard.session",
  "dashboard.chat",
  "dashboard.validation",
  "dashboard.progress",
  "dashboard.settings",
]

export const rootMessages = (locale: string) => pickMessages(locale, root)

export const authMessages = (locale: string) =>
  pickMessages(locale, [...root, "dashboard.auth"])

export const appMessages = (locale: string) => pickMessages(locale, app)

export const adminMessages = (locale: string) =>
  pickMessages(locale, [...app, "dashboard.admin"])

export const instructorMessages = (locale: string) =>
  pickMessages(locale, [...app, "dashboard.instructor"])
