import React from "react";
import { AlertCircle, BarChart3, Loader } from "lucide-react";
import { AreaChart } from "../ui/area-chart";
import { BarChart } from "../ui/bar-chart";
import { DonutChart } from "../ui/pie-chart";

type ChartSeries = { name: string; data: number[] };

type ValueFormat = "currency_usd" | "rating" | "number";

type ChartPayload = {
  type: "bar" | "line" | "pie";
  title: string;
  categories: string[];
  series: ChartSeries[];
  value_format?: ValueFormat;
};

type ChartErrorPayload = { error: string };

type ChartRendererProps = {
  status: "executing" | "inProgress" | "complete";
  result: string | undefined;
};

const CHART_COLORS = [
  "#3b82f6",
  "#10b981",
  "#6366f1",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#059669",
  "#f97316",
];

function parseChartResult(
  result: string | undefined,
): ChartPayload | ChartErrorPayload | null {
  if (!result) return null;
  try {
    const parsed = JSON.parse(result);
    if (!parsed || typeof parsed !== "object") return null;
    if (typeof parsed.error === "string") {
      return { error: parsed.error };
    }
    if (Array.isArray(parsed.categories) && Array.isArray(parsed.series)) {
      return parsed as ChartPayload;
    }
    return null;
  } catch {
    return null;
  }
}

function toRows(payload: ChartPayload): Record<string, string | number>[] {
  return payload.categories.map((category, i) => {
    const row: Record<string, string | number> = { name: category };
    for (const series of payload.series) {
      row[series.name] = series.data[i] ?? 0;
    }
    return row;
  });
}

const VALUE_FORMATTERS: Record<ValueFormat, (value: number) => string> = {
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

/**
 * Renders the structured JSON returned by the agent's `plot_chart` tool
 * (see agent/tools.py) as a real bar, line, or donut chart, reusing this
 * app's existing Recharts-based chart primitives. The tool's `value_format`
 * hint picks the right number formatting (a movie's rating isn't a currency).
 */
export function ChartRenderer({ status, result }: ChartRendererProps) {
  const payload = parseChartResult(result);
  const valueFormatter =
    payload && "value_format" in payload
      ? VALUE_FORMATTERS[payload.value_format ?? "number"]
      : VALUE_FORMATTERS.number;

  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <BarChart3 className="h-4 w-4 text-blue-500" />
        <h3 className="text-sm font-medium">
          {payload && "title" in payload ? payload.title : "Chart"}
        </h3>
      </div>

      {(status === "executing" || status === "inProgress") && (
        <div className="flex items-center gap-2 text-xs text-blue-500">
          <Loader className="h-3 w-3 animate-spin" />
          <span>Building chart...</span>
        </div>
      )}

      {status === "complete" && payload && "error" in payload && (
        <div className="flex items-center gap-2 text-sm text-red-500">
          <AlertCircle className="h-3 w-3" />
          <span>{payload.error}</span>
        </div>
      )}

      {status === "complete" && payload && "type" in payload && (
        <div className="h-64">
          {payload.type === "bar" && (
            <BarChart
              data={toRows(payload)}
              index="name"
              categories={payload.series.map((s) => s.name)}
              colors={CHART_COLORS}
              valueFormatter={valueFormatter}
              showLegend={payload.series.length > 1}
              showGrid
              layout="horizontal"
            />
          )}
          {payload.type === "line" && (
            <AreaChart
              data={toRows(payload)}
              index="name"
              categories={payload.series.map((s) => s.name)}
              colors={CHART_COLORS}
              valueFormatter={valueFormatter}
              showLegend={payload.series.length > 1}
              showGrid
              showXAxis
              showYAxis
            />
          )}
          {payload.type === "pie" && (
            <DonutChart
              data={toRows(payload)}
              category={payload.series[0]?.name ?? "value"}
              index="name"
              colors={CHART_COLORS}
              valueFormatter={valueFormatter}
              showLegend
              innerRadius={45}
              outerRadius="90%"
            />
          )}
        </div>
      )}

      {status === "complete" && !payload && (
        <p className="text-sm text-gray-500">No chart data was returned.</p>
      )}
    </div>
  );
}
