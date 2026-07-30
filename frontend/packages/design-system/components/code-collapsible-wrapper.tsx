"use client"

import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@repo/design-system/ui/collapsible"
import { Separator } from "@repo/design-system/ui/separator"
import * as React from "react"

export function CodeCollapsibleWrapper({
  className,
  children,
  labelCollapse = "Collapse",
  labelExpand = "Expand",
  ...props
}: React.ComponentProps<typeof Collapsible> & {
  labelCollapse?: string
  labelExpand?: string
}) {
  const [isOpened, setIsOpened] = React.useState(false)

  return (
    <Collapsible
      open={isOpened}
      onOpenChange={setIsOpened}
      className={cn("group/collapsible relative md:-mx-1", className)}
      {...props}
    >
      <CollapsibleTrigger
        nativeButton={false}
        render={
          <div className="absolute top-1.5 right-9 z-10 flex items-center" />
        }
      >
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground h-7 rounded-none px-2"
        >
          {isOpened ? labelCollapse : labelExpand}
        </Button>
        <Separator orientation="vertical" className="mx-1.5 !h-4" />
      </CollapsibleTrigger>
      <CollapsibleContent
        keepMounted
        hidden={false}
        className={cn(
          "relative mt-6 overflow-hidden [&>figure]:mt-0 [&>figure]:md:!mx-0",
          !isOpened && "max-h-64"
        )}
      >
        {children}
      </CollapsibleContent>
      <CollapsibleTrigger
        className={cn(
          "from-code/70 to-code text-muted-foreground absolute inset-x-0 -bottom-2 flex h-20 items-center justify-center rounded-none bg-gradient-to-b text-sm",
          isOpened && "hidden"
        )}
      >
        {isOpened ? labelCollapse : labelExpand}
      </CollapsibleTrigger>
    </Collapsible>
  )
}
