"use client";

import { useRenderTool } from "@copilotkit/react-core/v2";
import { z } from "zod";
import { ChartRenderer } from "../generative-ui/ChartRenderer";

// Só o resultado é desenhado, então os argumentos da chamada não são validados.
const anyArguments = z.object({}).passthrough();

/** Registra o desenho do resultado de uma ferramenta de gráfico do backend. */
function useChartTool(name: string) {
  useRenderTool({
    name,
    parameters: anyArguments,
    render: ({ status, result }) => (
      <ChartRenderer status={status} result={result} />
    ),
  });
}

/**
 * Ferramentas de gráfico do agente (agent/imdb/tools.py). Todas devolvem o
 * mesmo tipo de JSON e por isso usam o mesmo componente de desenho.
 */
export function useChartTools() {
  useChartTool("plot_chart");
  useChartTool("plot_distribution");
  useChartTool("plot_scatter");
  useChartTool("plot_top_movies");
}
