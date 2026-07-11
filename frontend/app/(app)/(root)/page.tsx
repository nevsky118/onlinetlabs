import { ArrowUpRightIcon } from "lucide-react"
import type { Metadata } from "next"
import Link from "next/link"
import { version } from "../../../package.json"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"

export const metadata: Metadata = {
  title: "Главная",
  description:
    "Обучение, которое видит вашу лабу. Агенты видят контекст среды и помогают прямо по нему — пока вы учитесь.",
}

const hatch =
  "bg-[image:repeating-linear-gradient(315deg,_var(--pattern-fg)_0,_var(--pattern-fg)_1px,_transparent_0,_transparent_50%)] bg-[size:10px_10px] [--pattern-fg:var(--color-foreground)]/5"

const displayVersion = `v${version.split(".").slice(0, 2).join(".")}`

export default function Home() {
  return (
    <section className="container-wrapper 3xl:fixed:px-0 flex flex-1 flex-col px-6">
      <div className="3xl:fixed:container relative flex flex-1 flex-col">
        <section className="relative flex flex-1 flex-col overflow-hidden">
          <div
            aria-hidden
            className={cn(
              "absolute inset-0 [mask-image:linear-gradient(to_top,black,transparent_55%)]",
              hatch
            )}
          />

          <div className="relative flex flex-1 flex-col justify-between gap-10 px-6 py-8 sm:px-10">
            <div className="my-auto flex flex-col gap-8 pt-6">
              <h1 className="animate-in fade-in-0 slide-in-from-bottom-2 fill-mode-both text-[clamp(2.4rem,6vw,5.5rem)] leading-[0.98] font-semibold tracking-[-0.03em] uppercase delay-75 duration-700 motion-reduce:animate-none">
                <span className="block">Обучение,</span>
                <span className="block">
                  которое{" "}
                  <span className="text-transparent [-webkit-text-stroke:1.5px_var(--color-foreground)]">
                    видит
                  </span>
                </span>
                <span className="block">вашу лабу</span>
              </h1>

              <p className="text-muted-foreground animate-in fade-in-0 slide-in-from-bottom-2 fill-mode-both max-w-md text-base leading-relaxed text-pretty delay-150 duration-700 motion-reduce:animate-none sm:text-lg">
                Агенты видят контекст вашей среды и помогают прямо по нему —
                пока вы учитесь.
              </p>

              <div className="animate-in fade-in-0 slide-in-from-bottom-2 fill-mode-both flex flex-wrap items-center gap-3 delay-200 duration-700 motion-reduce:animate-none">
                <Button
                  nativeButton={false}
                  size="lg"
                  className="h-11 px-6 text-sm"
                  render={<Link href="/courses" />}
                >
                  Курсы
                  <ArrowUpRightIcon data-icon="inline-end" />
                </Button>
                <Button
                  nativeButton={false}
                  size="lg"
                  variant="outline"
                  className="h-11 px-6 text-sm"
                  render={<Link href="/labs" />}
                >
                  Лабы
                </Button>
              </div>
            </div>

            <div className="text-muted-foreground animate-in fade-in-0 fill-mode-both flex items-center justify-between gap-4 font-mono text-xs tracking-[0.2em] uppercase delay-300 duration-700 motion-reduce:animate-none">
              <span className="inline-flex items-center gap-2.5">
                <span
                  aria-hidden
                  className="bg-foreground inline-block size-1 motion-safe:animate-pulse"
                />
                gns3 · docker · субд
              </span>
              <span>{displayVersion}</span>
            </div>
          </div>
        </section>
      </div>
    </section>
  )
}
