import { AlertTriangleIcon, WifiOffIcon } from "lucide-react"
import type { StreamStatus } from "../types"
import { Alert, AlertDescription } from "@/ui/alert"

export function StreamStatusBanner({ status }: { status: StreamStatus }) {
  if (status === "live") return null

  const config = {
    connecting: {
      Icon: WifiOffIcon,
      text: "Соединение с live-потоком восстанавливается...",
    },
    degraded: {
      Icon: AlertTriangleIcon,
      text: "Live-данные временно недоступны, пытаемся восстановить",
    },
    polling: {
      Icon: WifiOffIcon,
      text: "Live-поток недоступен. Обновляем данные каждые 10 секунд.",
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
