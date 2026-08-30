import { useTranslations } from "next-intl"

// Monochrome confusion matrix, cell shade via opacity on bg-foreground
type Props = {
  confusion: Record<string, Record<string, number>>
}

function maxValue(confusion: Record<string, Record<string, number>>): number {
  let max = 0
  for (const row of Object.values(confusion)) {
    for (const value of Object.values(row)) {
      if (value > max) max = value
    }
  }
  return max
}

export function ConfusionGrid({ confusion }: Props) {
  const t = useTranslations("dashboard.admin.confusionGrid")
  const regimes = Object.keys(confusion)
  const detected = Array.from(
    new Set(regimes.flatMap((regime) => Object.keys(confusion[regime] ?? {})))
  )
  const top = maxValue(confusion)

  if (regimes.length === 0) {
    return <p className="text-sm text-muted-foreground">{t("unavailable")}</p>
  }

  return (
    <div className="overflow-x-auto">
      <table
        className="w-full border-collapse text-xs tabular-nums"
        aria-label={t("ariaLabel")}
      >
        <thead>
          <tr>
            <th
              scope="col"
              className="border px-2 py-1 text-left font-medium text-muted-foreground"
            >
              {t("axisLabel")}
            </th>
            {detected.map((col) => (
              <th
                key={col}
                scope="col"
                className="border px-2 py-1 text-center font-medium text-muted-foreground"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {regimes.map((truth) => (
            <tr key={truth}>
              <th
                scope="row"
                className="border px-2 py-1 text-left font-medium text-muted-foreground"
              >
                {truth}
              </th>
              {detected.map((det) => {
                const count = confusion[truth]?.[det] ?? 0
                const opacity = top > 0 ? count / top : 0
                const isDiag = truth === det
                return (
                  <td
                    key={`${truth}-${det}`}
                    aria-label={t("cellAriaLabel", {
                      truth,
                      detected: det,
                      count,
                    })}
                    className={[
                      "relative border px-2 py-1 text-center",
                      isDiag ? "border-2 border-foreground" : "",
                    ]
                      .join(" ")
                      .trim()}
                  >
                    {/* Background shade */}
                    <span
                      aria-hidden="true"
                      className="pointer-events-none absolute inset-0 bg-foreground"
                      style={{ opacity: opacity * 0.45 }}
                    />
                    <span className="relative">{count}</span>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-1 text-xs text-muted-foreground">{t("caption")}</p>
    </div>
  )
}
