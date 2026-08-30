"use client"

import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@repo/design-system/ui/tooltip"
import { CheckIcon, CopyIcon } from "lucide-react"
import * as React from "react"

export type CopyEvent = {
  name: string
  properties?: Record<string, string | number | boolean | null>
}

export function copyToClipboardWithMeta(
  value: string,
  event?: CopyEvent,
  onTrack?: (event: CopyEvent) => void
) {
  navigator.clipboard.writeText(value)
  if (event) {
    onTrack?.(event)
  }
}

export function CopyButton({
  value,
  className,
  variant = "ghost",
  event,
  onCopied,
  labelCopy = "Copy",
  labelCopied = "Copied",
  ...props
}: React.ComponentProps<typeof Button> & {
  value: string
  src?: string
  event?: string
  onCopied?: (event: CopyEvent) => void
  labelCopy?: string
  labelCopied?: string
}) {
  const [hasCopied, setHasCopied] = React.useState(false)

  React.useEffect(() => {
    setTimeout(() => {
      setHasCopied(false)
    }, 2000)
  }, [])

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Button
            data-slot="copy-button"
            size="icon"
            variant={variant}
            className={cn(
              "absolute top-3 right-2 z-10 size-7 bg-code hover:opacity-100 focus-visible:opacity-100",
              className
            )}
            onClick={() => {
              copyToClipboardWithMeta(
                value,
                event
                  ? {
                      name: event,
                      // code can be large, cut to 500 characters to fit the properties limit
                      properties: { code: String(value).slice(0, 500) },
                    }
                  : undefined,
                onCopied
              )
              setHasCopied(true)
            }}
            {...props}
          />
        }
      >
        <span className="sr-only">{labelCopy}</span>
        {hasCopied ? <CheckIcon /> : <CopyIcon />}
      </TooltipTrigger>
      <TooltipContent>{hasCopied ? labelCopied : labelCopy}</TooltipContent>
    </Tooltip>
  )
}
