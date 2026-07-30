import { cn } from "@repo/design-system/lib/utils"
import { Badge } from "@repo/design-system/ui/badge"
import Link from "next/link"
import { getTranslations } from "next-intl/server"

type ContentCardProps = React.ComponentProps<typeof Link> & {
  title: string
  description: string
  tasks?: number
  difficulty?: "easy" | "medium" | "hard"
  tags?: string[]
}

export const ContentCard = async ({
  title,
  description,
  tasks,
  difficulty,
  tags,
  className,
  ...props
}: ContentCardProps) => {
  const t = await getTranslations("web.contentCard")

  return (
    <Link
      className={cn(
        "group relative flex h-full flex-col p-4 border bg-background shadow-xs hover:bg-accent dark:border-input dark:hover:bg-accent/50 transition-all",
        className
      )}
      {...props}
    >
      {(tasks || difficulty) && (
        <div className="mb-1">
          {tasks && (
            <p className="text-muted-foreground m-0 inline-block text-xs after:px-[0.33em] after:content-['•']">
              {t("tasksCount", { count: tasks })}
            </p>
          )}
          {difficulty && (
            <p className="text-muted-foreground m-0 inline-block text-xs">
              {t(`difficulty.${difficulty}`)}
            </p>
          )}
        </div>
      )}
      <header className="h-14">
        <h2 className="text-xl">{title}</h2>
      </header>
      <div className="flex content-center overflow-hidden rounded-none py-5">
        <div className="h-[132px] w-full border-x border-x-(--pattern-fg) bg-[repeating-linear-gradient(315deg,var(--pattern-fg)_0,var(--pattern-fg)_1px,transparent_0,transparent_50%)] bg-size-[10px_10px] bg-fixed [--pattern-fg:var(--color-foreground)]/5"></div>
      </div>
      {tags && tags.length > 0 && (
        <footer className="mt-auto flex flex-wrap items-center gap-2">
          {tags.map((tag) => (
            <Badge
              key={tag}
              variant="outline"
              className="rounded-none uppercase"
            >
              {tag}
            </Badge>
          ))}
        </footer>
      )}
    </Link>
  )
}
