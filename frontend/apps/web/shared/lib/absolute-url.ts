import { webUrl } from "./urls"

export function absoluteUrl(path: string) {
  return `${webUrl}${path}`
}
