"use client"

import { CheckIcon, CopyIcon } from "lucide-react"
import * as React from "react"
import { trackCustom } from "@/lib/analytics"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/ui/tooltip"

type CopyEvent = {
  name: string
  properties?: Record<string, string | number | boolean | null>
}

export function copyToClipboardWithMeta(value: string, event?: CopyEvent) {
  navigator.clipboard.writeText(value)
  if (event) {
    trackCustom(event.name, event.properties ?? {})
  }
}

export function CopyButton({
  value,
  className,
  variant = "ghost",
  event,
  ...props
}: React.ComponentProps<typeof Button> & {
  value: string
  src?: string
  event?: string
}) {
  const [hasCopied, setHasCopied] = React.useState(false)

  React.useEffect(() => {
    setTimeout(() => {
      setHasCopied(false)
    }, 2000)
  }, [])

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          data-slot="copy-button"
          size="icon"
          variant={variant}
          className={cn(
            "bg-code absolute top-3 right-2 z-10 size-7 hover:opacity-100 focus-visible:opacity-100",
            className
          )}
          onClick={() => {
            copyToClipboardWithMeta(
              value,
              event
                ? {
                    name: event,
                    // код может быть большим, режем до 500 символов под лимит properties
                    properties: { code: String(value).slice(0, 500) },
                  }
                : undefined
            )
            setHasCopied(true)
          }}
          {...props}
        >
          <span className="sr-only">Копировать</span>
          {hasCopied ? <CheckIcon /> : <CopyIcon />}
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        {hasCopied ? "Скопировано" : "Скопировать"}
      </TooltipContent>
    </Tooltip>
  )
}
