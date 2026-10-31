"use client";

import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  CHART_COLORS,
  VALUE_FORMATTERS,
  type ScatterChartPayload,
} from "./chart-types";

/** Campos muito assimétricos (votos, bilheteria) ficam ilegíveis em escala linear. */
function useLogScale(values: number[]): boolean {
  const positive = values.filter((v) => v > 0);
  if (positive.length !== values.length || positive.length === 0) return false;
  return Math.max(...positive) / Math.min(...positive) > 1000;
}

export function ScatterPlot({ chart }: { chart: ScatterChartPayload }) {
  const formatX = VALUE_FORMATTERS[chart.x_format ?? "number"];
  const formatY = VALUE_FORMATTERS[chart.y_format ?? "number"];
  const xLog = useLogScale(chart.points.map((p) => p.x));
  const yLog = useLogScale(chart.points.map((p) => p.y));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 10, right: 16, left: 10, bottom: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          type="number"
          dataKey="x"
          name={chart.x_label}
          tickFormatter={formatX}
          scale={xLog ? "log" : "auto"}
          domain={["auto", "auto"]}
          tick={{ fill: "#6b7280", fontSize: 12 }}
          label={{
            value: xLog ? `${chart.x_label} (log)` : chart.x_label,
            position: "insideBottom",
            offset: -12,
            fill: "#6b7280",
            fontSize: 12,
          }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name={chart.y_label}
          tickFormatter={formatY}
          scale={yLog ? "log" : "auto"}
          domain={["auto", "auto"]}
          width={70}
          tick={{ fill: "#6b7280", fontSize: 12 }}
        />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            const point = active ? payload?.[0]?.payload : undefined;
            if (!point) return null;
            return (
              <div className="rounded-md border border-gray-200 bg-white px-3 py-2 text-xs shadow-sm">
                <div className="font-medium">{point.label}</div>
                <div>
                  {chart.x_label}: {formatX(point.x)}
                </div>
                <div>
                  {chart.y_label}: {formatY(point.y)}
                </div>
              </div>
            );
          }}
        />
        <Scatter
          data={chart.points}
          fill={CHART_COLORS[0]}
          fillOpacity={0.45}
          isAnimationActive={false}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
