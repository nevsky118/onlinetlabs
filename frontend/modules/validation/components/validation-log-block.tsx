"use client"

export function ValidationLogBlock({ text }: { text: string }) {
  return (
    <pre className="font-mono text-xs bg-muted px-3 py-2 whitespace-pre-wrap break-all">
      {text}
    </pre>
  )
}
