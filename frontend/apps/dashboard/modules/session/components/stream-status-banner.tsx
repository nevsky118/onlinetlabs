import { Alert, AlertDescription } from "@repo/design-system/ui/alert"
import { AlertTriangleIcon, WifiOffIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import type { StreamStatus } from "../types"

export function StreamStatusBanner({ status }: { status: StreamStatus }) {
  const t = useTranslations("dashboard.session.streamStatusBanner")

  if (status === "live") return null

  const config = {
    connecting: {
      Icon: WifiOffIcon,
      text: t("connecting"),
    },
    degraded: {
      Icon: AlertTriangleIcon,
      text: t("degraded"),
    },
    polling: {
      Icon: WifiOffIcon,
      text: t("polling", { seconds: 10 }),
    },
  }[status]
  const Icon = config.Icon

  return (
    <Alert className="rounded-none">
      <Icon className="size-4" />
      <AlertDescription>{config.text}</AlertDescription>
    </Alert>
  )
}
