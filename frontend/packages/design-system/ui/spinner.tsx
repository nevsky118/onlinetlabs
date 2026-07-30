import { cn } from "@repo/design-system/lib/utils"
import { Loader2Icon } from "lucide-react"

function Spinner({
  className,
  labelLoading = "Loading",
  ...props
}: React.ComponentProps<"svg"> & { labelLoading?: string }) {
  return (
    <Loader2Icon
      role="status"
      aria-label={labelLoading}
      className={cn("size-4 animate-spin", className)}
      {...props}
    />
  )
}

export { Spinner }
