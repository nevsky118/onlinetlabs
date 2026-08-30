"use client"

import { getDashboardDestinations } from "@/lib/config"
import { Dialog as DialogPrimitive } from "@base-ui/react/dialog"
import { copyToClipboardWithMeta } from "@repo/design-system/components/copy-button"
import { useMutationObserver } from "@repo/design-system/hooks/use-mutation-observer"
import { cn } from "@repo/design-system/lib/utils"
import { Button } from "@repo/design-system/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@repo/design-system/ui/command"
import {
  Dialog,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
  DialogTrigger,
} from "@repo/design-system/ui/dialog"
import { Separator } from "@repo/design-system/ui/separator"
import { ArrowRightIcon, CornerDownLeftIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { useRouter } from "next/navigation"
import * as React from "react"

export function CommandMenu({
  navItems,
  ...props
}: React.ComponentProps<typeof Button> & {
  navItems?: { href: string; label: string }[]
}) {
  const t = useTranslations("dashboard.app.commandMenu")
  const locale = useLocale()
  const router = useRouter()
  const dashboardDestinations = React.useMemo(
    () => getDashboardDestinations(t, locale),
    [t, locale]
  )
  const [open, setOpen] = React.useState(false)
  const [selectedType, setSelectedType] = React.useState<"page" | null>(null)
  const [copyPayload, setCopyPayload] = React.useState("")

  const commandFilter = React.useCallback(
    (value: string, searchValue: string, keywords?: string[]) => {
      const extendValue = `${value} ${keywords?.join(" ") || ""}`
      if (extendValue.toLowerCase().includes(searchValue.toLowerCase())) {
        return 1
      }
      return 0
    },
    []
  )

  const runCommand = React.useCallback((command: () => unknown) => {
    setOpen(false)
    command()
  }, [])

  const navItemsSection = React.useMemo(() => {
    if (!navItems || navItems.length === 0) {
      return null
    }

    return (
      <CommandGroup
        heading={t("pagesHeading")}
        className="p-0! **:[[cmdk-group-heading]]:scroll-mt-16 **:[[cmdk-group-heading]]:p-3! **:[[cmdk-group-heading]]:pb-1!"
      >
        {navItems.map((item) => (
          <CommandMenuItem
            key={item.href}
            value={`Navigation ${item.label}`}
            keywords={["nav", "navigation", item.label.toLowerCase()]}
            onHighlight={() => {
              setSelectedType("page")
              setCopyPayload(item.href)
            }}
            onSelect={() => {
              runCommand(() => router.push(item.href))
            }}
          >
            <ArrowRightIcon />
            {item.label}
          </CommandMenuItem>
        ))}
      </CommandGroup>
    )
  }, [navItems, runCommand, router, t])

  // Static list of dashboard sections
  const destinationsSection = React.useMemo(
    () => (
      <CommandGroup
        heading={t("sectionsHeading")}
        className="p-0! **:[[cmdk-group-heading]]:scroll-mt-16 **:[[cmdk-group-heading]]:p-3! **:[[cmdk-group-heading]]:pb-1!"
      >
        {dashboardDestinations.map((item) => (
          <CommandMenuItem
            key={item.href}
            value={item.name}
            onHighlight={() => {
              setSelectedType("page")
              setCopyPayload(item.href)
            }}
            onSelect={() => {
              runCommand(() => router.push(item.href))
            }}
          >
            <ArrowRightIcon />
            {item.name}
          </CommandMenuItem>
        ))}
      </CommandGroup>
    ),
    [runCommand, router, t, dashboardDestinations]
  )

  React.useEffect(() => {
    const down = (event: KeyboardEvent) => {
      if (
        (event.key === "k" && (event.metaKey || event.ctrlKey)) ||
        event.key === "/"
      ) {
        if (
          (event.target instanceof HTMLElement &&
            event.target.isContentEditable) ||
          event.target instanceof HTMLInputElement ||
          event.target instanceof HTMLTextAreaElement ||
          event.target instanceof HTMLSelectElement
        ) {
          return
        }

        event.preventDefault()
        setOpen((isOpen) => !isOpen)
      }

      if (event.key === "c" && (event.metaKey || event.ctrlKey)) {
        runCommand(() => {
          if (selectedType === "page" && copyPayload) {
            copyToClipboardWithMeta(copyPayload)
          }
        })
      }
    }

    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [copyPayload, runCommand, selectedType])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button
            variant="outline"
            className={cn(
              "relative h-8 w-full justify-start rounded-none border-none bg-muted pl-3 text-foreground shadow-none transition-colors hover:bg-muted/50 md:w-48 lg:w-40 xl:w-64 dark:bg-card"
            )}
            onClick={() => setOpen(true)}
            {...props}
          />
        }
      >
        <span className="hidden xl:inline-flex">{t("placeholder")}</span>
        <span className="inline-flex xl:hidden">{t("placeholderShort")}</span>
      </DialogTrigger>
      <DialogContent className="rounded-none border-none bg-clip-padding p-2 pb-11 shadow-2xl ring-4 ring-neutral-200/80 dark:bg-neutral-900 dark:ring-neutral-800">
        <DialogHeader className="sr-only">
          <DialogTitle>{t("placeholder")}</DialogTitle>
        </DialogHeader>
        <Command
          className="rounded-none bg-transparent **:data-[slot=command-input]:h-8! **:data-[slot=command-input]:py-0 **:data-[slot=command-input-wrapper]:mb-0 **:data-[slot=command-input-wrapper]:h-8! **:data-[slot=command-input-wrapper]:rounded-none **:data-[slot=command-input-wrapper]:border **:data-[slot=command-input-wrapper]:border-input **:data-[slot=command-input-wrapper]:bg-input/50"
          filter={commandFilter}
        >
          <CommandInput placeholder={t("placeholder")} />
          <CommandList className="no-scrollbar min-h-80 scroll-pt-2 scroll-pb-1.5">
            <CommandEmpty className="py-12 text-center text-sm text-muted-foreground">
              {t("noResults")}
            </CommandEmpty>
            {navItemsSection}
            {destinationsSection}
          </CommandList>
        </Command>
        <div className="absolute inset-x-0 bottom-0 z-20 flex h-10 items-center gap-2 rounded-none border-t border-t-neutral-100 bg-neutral-50 px-4 text-xs font-medium text-muted-foreground dark:border-t-neutral-700 dark:bg-neutral-800">
          <div className="flex items-center gap-2">
            <CommandMenuKbd>
              <CornerDownLeftIcon />
            </CommandMenuKbd>{" "}
            {selectedType === "page" ? t("goToPage") : null}
          </div>
          {copyPayload && (
            <>
              <Separator orientation="vertical" className="h-4!" />
              <div className="flex items-center gap-1">
                <CommandMenuKbd>⌘</CommandMenuKbd>
                <CommandMenuKbd>C</CommandMenuKbd>
                {copyPayload}
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

function CommandMenuItem({
  children,
  className,
  onHighlight,
  ...props
}: React.ComponentProps<typeof CommandItem> & {
  onHighlight?: () => void
  "data-selected"?: string
  "aria-selected"?: string
}) {
  const ref = React.useRef<HTMLDivElement>(null)

  useMutationObserver(ref, (mutations) => {
    mutations.forEach((mutation) => {
      if (
        mutation.type === "attributes" &&
        mutation.attributeName === "aria-selected" &&
        ref.current?.getAttribute("aria-selected") === "true"
      ) {
        onHighlight?.()
      }
    })
  })

  return (
    <CommandItem
      ref={ref}
      className={cn(
        "h-9 rounded-none border border-transparent px-3! font-medium data-[selected=true]:border-input data-[selected=true]:bg-input/50",
        className
      )}
      {...props}
    >
      {children}
    </CommandItem>
  )
}

function CommandMenuKbd({ className, ...props }: React.ComponentProps<"kbd">) {
  return (
    <kbd
      className={cn(
        "pointer-events-none flex h-5 items-center justify-center gap-1 rounded-none border bg-background px-1 font-sans text-[0.7rem] font-medium text-muted-foreground select-none [&_svg:not([class*='size-'])]:size-3",
        className
      )}
      {...props}
    />
  )
}

function DialogContent({
  className,
  children,
  ...props
}: DialogPrimitive.Popup.Props & {
  showCloseButton?: boolean
}) {
  return (
    <DialogPortal data-slot="dialog-portal">
      <DialogOverlay />
      <DialogPrimitive.Popup
        data-slot="dialog-content"
        className={cn(
          "fixed top-[15%] left-[50%] z-50 grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] gap-4 rounded-none border bg-background p-6 shadow-lg duration-200 outline-none sm:max-w-lg",
          className
        )}
        {...props}
      >
        {children}
      </DialogPrimitive.Popup>
    </DialogPortal>
  )
}
