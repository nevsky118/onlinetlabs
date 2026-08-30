"use client"

export function ValidationLogBlock({ text }: { text: string }) {
  return (
    <pre className="bg-muted px-3 py-2 font-mono text-xs break-all whitespace-pre-wrap">
      {text}
    </pre>
  )
}
