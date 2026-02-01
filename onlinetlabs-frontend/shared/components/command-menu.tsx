"use client"

import { useDocsSearch } from "fumadocs-core/search/client"
import { ArrowRightIcon, CornerDownLeftIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import * as React from "react"
import type { FumaDocsPageTree } from "@/lib/source"
import { copyToClipboardWithMeta } from "@/components/copy-button"
import { useIsMac } from "@/hooks/use-is-mac"
import { useMutationObserver } from "@/hooks/use-mutation-observer"
import { siteConfig } from "@/lib/config"
import { trackEvent } from "@/lib/events"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/ui/command"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/ui/dialog"
import { Kbd, KbdGroup } from "@/ui/kbd"
import { Separator } from "@/ui/separator"
import { Spinner } from "@/ui/spinner"

type DialogProps = React.ComponentProps<typeof Dialog>

export function CommandMenu({
  trees,
  blocks,
  navItems,
  ...props
}: DialogProps & {
  trees: Array<{ tree: FumaDocsPageTree; label: string }>
  blocks?: { name: string; description: string; categories: string[] }[]
  navItems?: { href: string; label: string }[]
}) {
  const router = useRouter()
  const isMac = useIsMac()
  const [open, setOpen] = React.useState(false)
  const [selectedType, setSelectedType] = React.useState<"page" | null>(null)
  const [copyPayload, setCopyPayload] = React.useState("")

  const { search, setSearch, query } = useDocsSearch({
    type: "fetch",
  })

  // Track search queries with debouncing to avoid excessive tracking.
  const searchTimeoutRef = React.useRef<NodeJS.Timeout | undefined>(undefined)
  const lastTrackedQueryRef = React.useRef<string>("")

  const trackSearchQuery = React.useCallback((query: string) => {
    const trimmedQuery = query.trim()

    // Only track if the query is different from the last tracked query and has content.
    if (trimmedQuery && trimmedQuery !== lastTrackedQueryRef.current) {
      lastTrackedQueryRef.current = trimmedQuery
      trackEvent({
        name: "search_query",
        properties: {
          query: trimmedQuery,
          query_length: trimmedQuery.length,
        },
      })
    }
  }, [])

  const handleSearchChange = React.useCallback(
    (value: string) => {
      // Clear existing timeout.
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }

      // Set new timeout to debounce both search and tracking.
      searchTimeoutRef.current = setTimeout(() => {
        setSearch(value)
        trackSearchQuery(value)
      }, 500)
    },
    [setSearch, trackSearchQuery]
  )

  // Cleanup timeout on unmount.
  React.useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [])

  const handlePageHighlight = React.useCallback(() => {
    setSelectedType("page")
    setCopyPayload("")
  }, [])

  const runCommand = React.useCallback((command: () => unknown) => {
    setOpen(false)
    command()
  }, [])

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || e.key === "/") {
        if (
          (e.target instanceof HTMLElement && e.target.isContentEditable) ||
          e.target instanceof HTMLInputElement ||
          e.target instanceof HTMLTextAreaElement ||
          e.target instanceof HTMLSelectElement
        ) {
          return
        }

        e.preventDefault()
        setOpen((open) => !open)
      }

      if (e.key === "c" && (e.metaKey || e.ctrlKey)) {
        runCommand(() => {
          if (selectedType === "page" || selectedType === "component") {
            copyToClipboardWithMeta(copyPayload, {
              name: "copy_npm_command",
              properties: { command: copyPayload },
            })
          }
        })
      }
    }

    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [copyPayload, runCommand, selectedType])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="secondary"
          className={cn(
            "bg-surface text-foreground dark:bg-card relative h-8 w-full justify-start pl-3 font-medium shadow-none sm:pr-12 md:w-48 lg:w-56 xl:w-64"
          )}
          onClick={() => setOpen(true)}
          {...props}
        >
          <span className="hidden lg:inline-flex">
            Найти на {siteConfig.name}...
          </span>
          <span className="inline-flex lg:hidden">Найти...</span>
          <div className="absolute top-1.5 right-1.5 hidden gap-1 sm:flex">
            <KbdGroup>
              <Kbd className="border">{isMac ? "⌘" : "Ctrl"}</Kbd>
              <Kbd className="border">K</Kbd>
            </KbdGroup>
          </div>
        </Button>
      </DialogTrigger>
      <DialogContent
        showCloseButton={false}
        className="rounded-xl border-none bg-clip-padding p-2 pb-11 shadow-2xl ring-4 ring-neutral-200/80 dark:bg-neutral-900 dark:ring-neutral-800"
      >
        <DialogHeader className="sr-only">
          <DialogTitle>Найти на {siteConfig.name}...</DialogTitle>
          {/* <DialogDescription>Search for a command to run...</DialogDescription> */}
        </DialogHeader>
        <Command
          className="**:data-[slot=command-input-wrapper]:bg-input/50 **:data-[slot=command-input-wrapper]:border-input rounded-none bg-transparent **:data-[slot=command-input]:!h-9 **:data-[slot=command-input]:py-0 **:data-[slot=command-input-wrapper]:mb-0 **:data-[slot=command-input-wrapper]:!h-9 **:data-[slot=command-input-wrapper]:rounded-md **:data-[slot=command-input-wrapper]:border"
          filter={(value, search, keywords) => {
            handleSearchChange(search)
            const extendValue = `${value} ${keywords?.join(" ") || ""}`
            if (extendValue.toLowerCase().includes(search.toLowerCase())) {
              return 1
            }
            return 0
          }}
        >
          <div className="relative">
            <CommandInput placeholder={`Найти на ${siteConfig.name}...`} />
            {query.isLoading && (
              <div className="pointer-events-none absolute top-1/2 right-3 z-10 flex -translate-y-1/2 items-center justify-center">
                <Spinner className="text-muted-foreground size-4" />
              </div>
            )}
          </div>
          <CommandList className="no-scrollbar min-h-80 scroll-pt-2 scroll-pb-1.5">
            <CommandEmpty className="text-muted-foreground py-12 text-center text-sm">
              {query.isLoading ? "Ищем..." : "Результатов не найдено."}
            </CommandEmpty>
            {navItems && navItems.length > 0 && (
              <CommandGroup
                heading="Pages"
                className="!p-0 [&_[cmdk-group-heading]]:scroll-mt-16 [&_[cmdk-group-heading]]:!p-3 [&_[cmdk-group-heading]]:!pb-1"
              >
                {navItems.map((item) => (
                  <CommandMenuItem
                    key={item.href}
                    value={`Navigation ${item.label}`}
                    keywords={["nav", "navigation", item.label.toLowerCase()]}
                    onHighlight={() => {
                      setSelectedType("page")
                      setCopyPayload("")
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
            )}
            {trees.map(({ tree, label }) =>
              tree.children.map((group) => (
                <CommandGroup
                  key={`${label}-${group.$id}`}
                  heading={`${label} - ${group.name}`}
                  className="!p-0 [&_[cmdk-group-heading]]:scroll-mt-16 [&_[cmdk-group-heading]]:!p-3 [&_[cmdk-group-heading]]:!pb-1"
                >
                  {group.type === "folder" &&
                    group.children.map((item) => {
                      if (item.type === "page") {
                        return (
                          <CommandMenuItem
                            key={item.url}
                            value={
                              item.name?.toString()
                                ? `${label} ${group.name} ${item.name}`
                                : ""
                            }
                            keywords={undefined}
                            onHighlight={() => handlePageHighlight()}
                            onSelect={() => {
                              runCommand(() => router.push(item.url))
                            }}
                          >
                            <ArrowRightIcon />
                            {item.name}
                          </CommandMenuItem>
                        )
                      }
                      return null
                    })}
                </CommandGroup>
              ))
            )}
            <SearchResults
              open={open}
              setOpen={setOpen}
              query={query}
              search={search}
            />
          </CommandList>
        </Command>
        <div className="text-muted-foreground absolute inset-x-0 bottom-0 z-20 flex h-10 items-center gap-2 rounded-b-xl border-t border-t-neutral-100 bg-neutral-50 px-4 text-xs font-medium dark:border-t-neutral-700 dark:bg-neutral-800">
          <div className="flex items-center gap-2">
            <CommandMenuKbd>
              <CornerDownLeftIcon />
            </CommandMenuKbd>{" "}
            {selectedType === "page" ? "Перейти на страницу" : null}
          </div>
          {copyPayload && (
            <>
              <Separator orientation="vertical" className="!h-4" />
              <div className="flex items-center gap-1">
                <CommandMenuKbd>{isMac ? "⌘" : "Ctrl"}</CommandMenuKbd>
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
        "data-[selected=true]:border-input data-[selected=true]:bg-input/50 h-9 rounded-md border border-transparent !px-3 font-medium",
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
        "bg-background text-muted-foreground pointer-events-none flex h-5 items-center justify-center gap-1 rounded border px-1 font-sans text-[0.7rem] font-medium select-none [&_svg:not([class*='size-'])]:size-3",
        className
      )}
      {...props}
    />
  )
}

type Query = Awaited<ReturnType<typeof useDocsSearch>>["query"]

function SearchResults({
  setOpen,
  query,
  search,
}: {
  open: boolean
  setOpen: (open: boolean) => void
  query: Query
  search: string
}) {
  const router = useRouter()

  const uniqueResults =
    query.data && Array.isArray(query.data)
      ? query.data.filter(
          (item, index, self) =>
            !(
              item.type === "text" &&
              item.content.trim().split(/\s+/).length <= 1
            ) && index === self.findIndex((t) => t.content === item.content)
        )
      : []

  if (!search.trim()) {
    return null
  }

  if (!query.data || query.data === "empty") {
    return null
  }

  if (query.data && uniqueResults.length === 0) {
    return null
  }

  return (
    <CommandGroup
      className="!px-0 [&_[cmdk-group-heading]]:scroll-mt-16 [&_[cmdk-group-heading]]:!p-3 [&_[cmdk-group-heading]]:!pb-1"
      heading="Search Results"
    >
      {uniqueResults.map((item) => {
        return (
          <CommandItem
            key={item.id}
            data-type={item.type}
            onSelect={() => {
              router.push(item.url)
              setOpen(false)
            }}
            className="data-[selected=true]:border-input data-[selected=true]:bg-input/50 h-9 rounded-md border border-transparent !px-3 font-normal"
            keywords={[item.content]}
            value={`${item.content} ${item.type}`}
          >
            <div className="line-clamp-1 text-sm">{item.content}</div>
          </CommandItem>
        )
      })}
    </CommandGroup>
  )
}
