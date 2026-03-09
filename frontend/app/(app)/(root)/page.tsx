import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Главная",
  description: "Доступ к курсам и лабораторным работам.",
}

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      Landing
    </div>
  )
}
