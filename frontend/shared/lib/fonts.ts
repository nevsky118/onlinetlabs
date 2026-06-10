import { Geist_Mono as FontMono, Inter as FontSans } from "next/font/google"
import { cn } from "@/lib/utils"

const fontSans = FontSans({
  subsets: ["latin", "cyrillic"],
  variable: "--font-sans",
})

const fontMono = FontMono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
})

export const fontVariables = cn(fontSans.variable, fontMono.variable)
