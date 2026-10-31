import React from "react";
import { AlertCircle, BarChart3, Loader } from "lucide-react";
import { AreaChart } from "../ui/area-chart";
import { BarChart } from "../ui/bar-chart";
import { DonutChart } from "../ui/pie-chart";
import { ScatterPlot } from "./ScatterPlot";
import {
  CHART_COLORS,
  VALUE_FORMATTERS,
  parseChartResult,
  type CategoryChart,
} from "./chart-types";

type ChartRendererProps = {
  status: "executing" | "inProgress" | "complete";
  result: string | undefined;
};

/** Uma linha por categoria, com uma coluna por série (formato do Recharts). */
function toRows(chart: CategoryChart): Record<string, string | number>[] {
  return chart.categories.map((category, i) => {
    const row: Record<string, string | number> = { name: category };
    for (const series of chart.series) {
      row[series.name] = series.data[i] ?? 0;
    }
    return row;
  });
}

/**
 * Barras na vertical só funcionam com poucos rótulos curtos. Com muitas
 * categorias ou rótulos longos (gêneros, títulos de filmes) usamos barras
 * horizontais, que deixam o texto legível.
 */
function chooseBarLayout(chart: CategoryChart) {
  const longest = Math.max(...chart.categories.map((c) => c.length), 0);
  const horizontalBars = chart.categories.length > 6 || longest > 12;
  return {
    // No componente BarChart, "vertical" significa barras deitadas.
    layout: horizontalBars ? ("vertical" as const) : ("horizontal" as const),
    labelWidth: Math.min(220, Math.max(90, longest * 6.5)),
    height: horizontalBars ? Math.max(256, chart.categories.length * 28 + 50) : 256,
  };
}

function CategoryChartView({ chart }: { chart: CategoryChart }) {
  const valueFormatter = VALUE_FORMATTERS[chart.value_format ?? "number"];
  const categories = chart.series.map((s) => s.name);
  const showLegend = chart.series.length > 1;
  const bars = chooseBarLayout(chart);
  const height = chart.type === "bar" ? bars.height : 256;

  return (
    <div style={{ height }}>
      {chart.type === "bar" && (
        <BarChart
          data={toRows(chart)}
          index="name"
          categories={categories}
          colors={CHART_COLORS}
          valueFormatter={valueFormatter}
          showLegend={showLegend}
          showGrid
          layout={bars.layout}
          yAxisWidth={bars.layout === "vertical" ? bars.labelWidth : 55}
        />
      )}
      {chart.type === "line" && (
        <AreaChart
          data={toRows(chart)}
          index="name"
          categories={categories}
          colors={CHART_COLORS}
          valueFormatter={valueFormatter}
          showLegend={showLegend}
          showGrid
          showXAxis
          showYAxis
        />
      )}
      {chart.type === "pie" && (
        <DonutChart
          data={toRows(chart)}
          category={categories[0] ?? "value"}
          index="name"
          colors={CHART_COLORS}
          valueFormatter={valueFormatter}
          showLegend
          innerRadius={45}
          outerRadius="90%"
        />
      )}
    </div>
  );
}

/**
 * Desenha o JSON devolvido pelas ferramentas plot_* do agente
 * (agent/imdb/charts.py) como gráfico interativo de barras, linha, pizza ou
 * dispersão. Os avisos do agente ("notes") aparecem abaixo do gráfico.
 */
export function ChartRenderer({ status, result }: ChartRendererProps) {
  const payload = parseChartResult(result);
  const chart = payload && "type" in payload ? payload : null;
  const error = payload && "error" in payload ? payload.error : null;
  const running = status === "executing" || status === "inProgress";

  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <BarChart3 className="h-4 w-4 text-blue-500" />
        <h3 className="text-sm font-medium">{chart?.title ?? "Chart"}</h3>
      </div>

      {running && (
        <div className="flex items-center gap-2 text-xs text-blue-500">
          <Loader className="h-3 w-3 animate-spin" />
          <span>Building chart...</span>
        </div>
      )}

      {status === "complete" && error && (
        <div className="flex items-center gap-2 text-sm text-red-500">
          <AlertCircle className="h-3 w-3" />
          <span>{error}</span>
        </div>
      )}

      {status === "complete" && chart && chart.type === "scatter" && (
        <div className="h-72">
          <ScatterPlot chart={chart} />
        </div>
      )}
      {status === "complete" && chart && chart.type !== "scatter" && (
        <CategoryChartView chart={chart} />
      )}

      {status === "complete" && chart?.notes && chart.notes.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-xs text-gray-500">
          {chart.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      )}

      {status === "complete" && !payload && (
        <p className="text-sm text-gray-500">No chart data was returned.</p>
      )}
    </div>
  );
}
