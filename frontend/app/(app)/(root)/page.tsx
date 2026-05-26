import { ArrowUpRightIcon } from "lucide-react"
import type { Metadata } from "next"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { Button } from "@/ui/button"

export const metadata: Metadata = {
  title: "Главная",
  description:
    "Платформа для адаптивных курсов поверх MCP с мультиагентной архитектурой.",
}

const hatch =
  "bg-[image:repeating-linear-gradient(315deg,_var(--pattern-fg)_0,_var(--pattern-fg)_1px,_transparent_0,_transparent_50%)] bg-[size:10px_10px] [--pattern-fg:var(--color-foreground)]/5"

const domains = [
  { name: "GNS3", note: "Сетевое администрирование", state: "пилот" },
  { name: "Docker", note: "Контейнеры", state: "next" },
  { name: "СУБД", note: "PostgreSQL · Oracle", state: "next" },
]

const feed = [
  { agent: "TutorAgent", action: "Объяснил настройку OSPF area 0" },
  { agent: "LabAgent", action: "ip ospf area 0 applied · r1" },
  { agent: "ValidatorAgent", action: "Шаг 3 / 5 пройден" },
  { agent: "AnalyticsAgent", action: "Класс: повтор ошибок" },
]

const classifier = [
  { cls: "Норма", bar: 9 },
  { cls: "Повтор ошибок", bar: 3 },
  { cls: "Хаотичный перебор", bar: 2 },
  { cls: "Бездействие", bar: 2 },
  { cls: "Застревание", bar: 2 },
]

const agents = [
  { name: "TutorAgent", role: "Тьютор" },
  { name: "AnalyticsAgent", role: "Аналитика" },
  { name: "LabAgent", role: "Действия в среде" },
  { name: "ValidatorAgent", role: "Валидация" },
  { name: "HintAgent", role: "Поддержка" },
]

export default function Home() {
  return (
    <section className="container-wrapper 3xl:fixed:px-0 flex flex-1 flex-col px-6">
      <div className="3xl:fixed:container border-border relative flex flex-1 flex-col border-x">
        <HeroSection />
        <BentoSection />
        <DomainsSection />
        <FinalCTASection />
      </div>
    </section>
  )
}

function HeroSection() {
  return (
    <section className="border-border relative overflow-hidden border-b">
      <div
        aria-hidden
        className={cn(
          "absolute inset-0 opacity-60 [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]",
          hatch
        )}
      />
      <SideGhost align="left" />
      <SideGhost align="right" />

      <div className="relative z-10 mx-auto flex max-w-3xl flex-col items-center gap-8 px-4 py-24 text-center sm:py-32 md:py-40 lg:py-44">
        <p className="border-border bg-background animate-in fade-in-0 slide-in-from-bottom-1 fill-mode-both inline-flex items-center gap-2.5 border px-3 py-1 font-mono text-[0.65rem] tracking-[0.22em] uppercase duration-500 motion-reduce:animate-none">
          <span
            aria-hidden
            className="bg-foreground inline-block size-1 motion-safe:animate-pulse"
          />
          onlinetlabs · v0.1
        </p>

        <h1 className="animate-in fade-in-0 slide-in-from-bottom-2 fill-mode-both text-[clamp(2.5rem,6.5vw,5.75rem)] leading-[0.95] font-semibold tracking-[-0.025em] text-balance delay-75 duration-700 motion-reduce:animate-none">
          Обучение, которое{" "}
          <span className="text-transparent [-webkit-text-stroke:1.5px_var(--color-foreground)]">
            видит
          </span>{" "}
          вашу&nbsp;систему.
        </h1>

        <p className="text-muted-foreground animate-in fade-in-0 slide-in-from-bottom-2 fill-mode-both max-w-xl text-base leading-relaxed text-pretty delay-150 duration-700 motion-reduce:animate-none sm:text-lg">
          Платформа для адаптивных курсов поверх MCP. Видит, что происходит в
          учебной среде, и подстраивает материал под действия студента.
        </p>

        <div className="animate-in fade-in-0 slide-in-from-bottom-2 fill-mode-both flex flex-wrap items-center justify-center gap-3 delay-200 duration-700 motion-reduce:animate-none">
          <Button asChild size="lg">
            <Link href="/courses">
              Каталог курсов
              <ArrowUpRightIcon data-icon="inline-end" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="ghost">
            <Link href="/labs">Практикумы</Link>
          </Button>
        </div>
      </div>
    </section>
  )
}

function SideGhost({ align }: { align: "left" | "right" }) {
  const isLeft = align === "left"
  return (
    <div
      aria-hidden
      className={cn(
        "animate-in fade-in-0 fill-mode-both pointer-events-none absolute top-1/2 hidden -translate-y-1/2 select-none opacity-[0.18] delay-300 duration-1000 motion-reduce:animate-none xl:block",
        isLeft ? "left-6 2xl:left-12" : "right-6 2xl:right-12"
      )}
    >
      <div className="border-border bg-background flex w-44 flex-col gap-2 border p-3 font-mono text-[0.55rem] tracking-widest uppercase">
        <span className="text-muted-foreground">
          {isLeft ? "mcp.state" : "session.live"}
        </span>
        <div className="bg-foreground/70 h-1.5 w-3/4" />
        <div className="bg-foreground/40 h-1.5 w-1/2" />
        <div className="bg-foreground/40 h-1.5 w-2/3" />
        <div className="bg-foreground/20 h-1.5 w-1/3" />
      </div>
      <div
        className={cn(
          "border-border bg-background mt-3 flex w-44 flex-col gap-1.5 border p-3 font-mono text-[0.55rem] tracking-widest uppercase",
          isLeft ? "ml-6" : "ml-[-1.5rem]"
        )}
      >
        <span className="text-muted-foreground">
          {isLeft ? "classifier" : "agents · 5"}
        </span>
        <div className="bg-foreground/60 h-1.5 w-2/3" />
        <div className="bg-foreground/30 h-1.5 w-1/2" />
        <div className="bg-foreground/30 h-1.5 w-1/3" />
      </div>
    </div>
  )
}

function BentoSection() {
  return (
    <section aria-labelledby="bento-heading" className="border-border border-b">
      <div className="text-muted-foreground flex items-center justify-between gap-4 px-6 py-4 font-mono text-[0.65rem] tracking-[0.22em] uppercase sm:px-10">
        <span id="bento-heading" className="text-foreground">
          / Внутри платформы
        </span>
      </div>

      <div className="bg-border border-border grid grid-cols-1 gap-px border-t md:grid-cols-3">
        <MockEventLog />
        <MockClassifier />
        <MockAgents />
      </div>
    </section>
  )
}

function MockCard({
  title,
  badge,
  children,
}: {
  title: string
  badge?: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-background flex flex-col p-6 sm:p-8">
      <div className="text-muted-foreground mb-5 flex items-center justify-between font-mono text-[0.65rem] tracking-[0.22em] uppercase">
        <span>{title}</span>
        {badge && (
          <span className="flex items-center gap-1.5">
            <span
              aria-hidden
              className="bg-foreground inline-block size-1 motion-safe:animate-pulse"
            />
            {badge}
          </span>
        )}
      </div>
      {children}
    </div>
  )
}

function MockEventLog() {
  return (
    <MockCard title="orchestrator.log" badge="live">
      <ul className="divide-border flex flex-1 flex-col divide-y font-mono text-[0.72rem]">
        {feed.map((line, i) => (
          <li
            key={line.agent}
            className="animate-in fade-in-0 slide-in-from-left-1 fill-mode-both flex flex-col gap-1 py-2.5 first:pt-0 last:pb-0 duration-500 motion-reduce:animate-none"
            style={{ animationDelay: `${300 + i * 100}ms` }}
          >
            <span className="text-muted-foreground/80 tracking-[0.18em] uppercase">
              {line.agent}
            </span>
            <span className="text-foreground leading-snug">
              → {line.action}
            </span>
          </li>
        ))}
      </ul>
    </MockCard>
  )
}

function MockClassifier() {
  return (
    <MockCard title="classifier">
      <ul className="flex flex-1 flex-col gap-3 font-mono text-[0.72rem]">
        {classifier.map((row) => (
          <li key={row.cls} className="flex flex-col gap-1.5">
            <span className="text-foreground">{row.cls}</span>
            <div className="bg-border h-1 w-full">
              <div
                className="bg-foreground h-1"
                style={{ width: `${(row.bar / 9) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </MockCard>
  )
}

function MockAgents() {
  return (
    <MockCard title="agents">
      <ul className="divide-border flex flex-1 flex-col divide-y font-mono text-[0.72rem]">
        {agents.map((a) => (
          <li
            key={a.name}
            className="flex items-baseline justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
          >
            <span className="text-foreground">{a.name}</span>
            <span className="text-muted-foreground">{a.role}</span>
          </li>
        ))}
      </ul>
    </MockCard>
  )
}

function DomainsSection() {
  return (
    <section
      aria-labelledby="domains-heading"
      className="border-border border-b"
    >
      <div className="text-muted-foreground flex items-center justify-between gap-4 px-6 py-4 font-mono text-[0.65rem] tracking-[0.22em] uppercase sm:px-10">
        <span id="domains-heading" className="text-foreground">
          / Домены
        </span>
      </div>

      <div className="grid grid-cols-1 border-t border-border md:grid-cols-[1fr_1.4fr]">
        <div className="border-border flex flex-col justify-center gap-4 p-8 sm:p-10 md:border-r">
          <h2 className="text-[clamp(1.5rem,2.2vw,2rem)] leading-[1.05] font-semibold tracking-[-0.02em] text-balance">
            Новый домен — это один MCP-сервер.
          </h2>
          <p className="text-muted-foreground text-sm leading-relaxed text-pretty">
            Ядро платформы остаётся прежним. Чтобы подключить другую среду,
            достаточно реализовать её MCP-сервер.
          </p>
        </div>

        <ul className="bg-border grid grid-cols-1 gap-px">
          {domains.map((d) => (
            <li
              key={d.name}
              className="bg-background hover:bg-muted/30 group flex items-center justify-between gap-4 px-6 py-5 transition-colors duration-150 ease-out sm:px-8"
            >
              <div className="flex flex-col gap-0.5">
                <span className="text-foreground text-base font-medium">
                  {d.name}
                </span>
                <span className="text-muted-foreground text-xs">{d.note}</span>
              </div>
              <span
                className={cn(
                  "font-mono text-[0.6rem] tracking-[0.22em] uppercase",
                  d.state === "пилот"
                    ? "bg-foreground text-background px-2 py-1"
                    : "border-border text-muted-foreground border px-2 py-1"
                )}
              >
                {d.state}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}

function FinalCTASection() {
  return (
    <section className={cn("relative overflow-hidden", hatch)}>
      <div className="relative z-10 mx-auto flex max-w-2xl flex-col items-center gap-6 px-6 py-20 text-center sm:py-24">
        <h2 className="text-[clamp(1.75rem,3.5vw,2.75rem)] leading-[1] font-semibold tracking-[-0.025em] text-balance">
          Откройте каталог и попробуйте.
        </h2>
        <Button asChild size="lg">
          <Link href="/courses">
            К каталогу курсов
            <ArrowUpRightIcon data-icon="inline-end" />
          </Link>
        </Button>
      </div>
    </section>
  )
}
