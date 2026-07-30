import { createNavigation } from "next-intl/navigation"
import { routing } from "./routing"

// Wrappers over next/link and next/navigation that inject the current locale.
export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing)
