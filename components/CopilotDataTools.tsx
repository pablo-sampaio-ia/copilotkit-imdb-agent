"use client";

import { useChartConfirmation } from "./tools/useChartConfirmation";
import { useChartTools } from "./tools/useChartTools";
import { usePythonAnalysisTool } from "./tools/usePythonAnalysisTool";

/**
 * Liga as ferramentas do agente à interface do chat. Cada hook em
 * `components/tools/` registra uma ferramenta:
 *
 * - useChartTools: ferramentas do backend que devolvem JSON de gráfico; o
 *   JSON vira um gráfico interativo ("tool rendering").
 * - usePythonAnalysisTool: ferramenta do backend; mostra código, texto e imagem.
 * - useChartConfirmation: ferramenta só do front-end (human-in-the-loop).
 *
 * Não renderiza nada: os hooks apenas registram as ferramentas no CopilotKit.
 */
export function CopilotDataTools() {
  useChartTools();
  usePythonAnalysisTool();
  useChartConfirmation();
  return null;
}
