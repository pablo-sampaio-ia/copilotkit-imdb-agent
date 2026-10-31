/**
 * Formato do JSON devolvido pelas ferramentas plot_* do agente
 * (ver agent/imdb/charts.py) e utilitários para lê-lo e formatá-lo.
 */

export type ValueFormat = "currency_usd" | "rating" | "number";

type ChartBase = { title: string; notes?: string[] };

/** bar, line e pie compartilham o mesmo formato (categorias + séries). */
export type CategoryChart = ChartBase & {
  type: "bar" | "line" | "pie";
  categories: string[];
  series: { name: string; data: number[] }[];
  value_format?: ValueFormat;
};

export type ScatterChartPayload = ChartBase & {
  type: "scatter";
  points: { x: number; y: number; label: string }[];
  x_label: string;
  y_label: string;
  x_format?: ValueFormat;
  y_format?: ValueFormat;
};

export type ChartPayload = CategoryChart | ScatterChartPayload;
export type ChartErrorPayload = { error: string };

/** Lê o resultado (string JSON) de uma ferramenta; null se não for um gráfico. */
export function parseChartResult(
  result: string | undefined,
): ChartPayload | ChartErrorPayload | null {
  if (!result) return null;
  try {
    const parsed = JSON.parse(result);
    if (!parsed || typeof parsed !== "object") return null;
    if (typeof parsed.error === "string") return { error: parsed.error };
    if (parsed.type === "scatter" && Array.isArray(parsed.points)) {
      return parsed as ScatterChartPayload;
    }
    if (Array.isArray(parsed.categories) && Array.isArray(parsed.series)) {
      return parsed as CategoryChart;
    }
    return null;
  } catch {
    return null;
  }
}

export const VALUE_FORMATTERS: Record<ValueFormat, (value: number) => string> = {
  currency_usd: (value) =>
    value.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
      notation: Math.abs(value) >= 1_000_000 ? "compact" : "standard",
    }),
  rating: (value) => value.toFixed(1),
  number: (value) => value.toLocaleString("en-US"),
};

export const CHART_COLORS = [
  "#3b82f6",
  "#10b981",
  "#6366f1",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#059669",
  "#f97316",
];
