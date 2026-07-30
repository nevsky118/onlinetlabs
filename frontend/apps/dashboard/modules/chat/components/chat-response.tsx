"use client"

import { cn } from "@repo/design-system/lib/utils"
import { type ComponentProps, memo } from "react"
import { Streamdown } from "streamdown"

type ResponseProps = ComponentProps<typeof Streamdown>

export const ChatResponse = memo(
  ({ className, ...props }: ResponseProps) => (
    <Streamdown
      className={cn(
        "size-full [&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
        // Lists get a uniform marker indent so items do not drift out of the text column.
        "[&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-1 [&_li]:marker:text-muted-foreground",
        className
      )}
      {...props}
    />
  ),
  (prev, next) => prev.children === next.children
)

ChatResponse.displayName = "ChatResponse"
