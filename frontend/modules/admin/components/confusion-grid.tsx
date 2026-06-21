// Монохром матрица путаницы — оттенок ячейки через opacity bg-foreground
type Props = {
  confusion: Record<string, Record<string, number>>
}

function maxValue(confusion: Record<string, Record<string, number>>): number {
  let max = 0
  for (const row of Object.values(confusion)) {
    for (const v of Object.values(row)) {
      if (v > max) max = v
    }
  }
  return max
}

export function ConfusionGrid({ confusion }: Props) {
  const regimes = Object.keys(confusion)
  const detected = Array.from(
    new Set(regimes.flatMap((r) => Object.keys(confusion[r] ?? {})))
  )
  const top = maxValue(confusion)

  if (regimes.length === 0) {
    return <p className="text-sm text-muted-foreground">Матрица недоступна</p>
  }

  return (
    <div className="overflow-x-auto">
      <table
        className="border-collapse text-xs tabular-nums w-full"
        aria-label="Матрица путаницы: строки — истинный режим, столбцы — определённый"
      >
        <thead>
          <tr>
            <th
              scope="col"
              className="border px-2 py-1 font-medium text-muted-foreground text-left"
            >
              ↓ истина \ определ. →
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
                className="border px-2 py-1 font-medium text-muted-foreground text-left"
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
                    aria-label={`истина=${truth} определ.=${det}: ${count}`}
                    className={[
                      "relative border px-2 py-1 text-center",
                      isDiag ? "border-2 border-foreground" : "",
                    ]
                      .join(" ")
                      .trim()}
                  >
                    {/* Фон-оттенок */}
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
      <p className="mt-1 text-xs text-muted-foreground">
        Строки — истинный режим, столбцы — определённый. Диагональ обведена.
      </p>
    </div>
  )
}
