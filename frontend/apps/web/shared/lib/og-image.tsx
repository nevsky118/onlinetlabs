import { ImageResponse } from "next/og"

export const ogSize = { width: 1200, height: 630 }

/** Catch-all segments cannot host opengraph-image.tsx, so the image lives on its own route. */
export function ogImagePath(
  locale: string,
  collection: "labs" | "courses",
  slug: string[]
) {
  return `/${locale}/og/${collection}/${slug.join("/")}`
}

function clamp(text: string, limit: number) {
  return text.length > limit ? `${text.slice(0, limit - 1).trimEnd()}…` : text
}

export function renderOgImage({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string
  title: string
  description?: string
}) {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        background: "#000000",
        color: "#ffffff",
        padding: "72px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
        <div style={{ width: "28px", height: "28px", background: "#ffffff" }} />
        <div style={{ fontSize: "26px", letterSpacing: "0.18em" }}>
          {eyebrow.toUpperCase()}
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
        <div style={{ fontSize: "68px", lineHeight: 1.1 }}>
          {clamp(title, 90)}
        </div>
        {description ? (
          <div style={{ fontSize: "30px", lineHeight: 1.4, color: "#a3a3a3" }}>
            {clamp(description, 150)}
          </div>
        ) : null}
      </div>
      <div
        style={{
          display: "flex",
          width: "160px",
          height: "6px",
          background: "#ffffff",
        }}
      />
    </div>,
    ogSize
  )
}
