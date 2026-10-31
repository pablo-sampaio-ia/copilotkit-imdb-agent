"use client";

import { useHumanInTheLoop } from "@copilotkit/react-core/v2";
import { z } from "zod";
import {
  ChartSpecConfirmation,
  type ChartSpecArgs,
} from "../generative-ui/ChartSpecConfirmation";

const AGENT_ID = "imdb_agent";

/**
 * `confirm_chart_spec` existe só no front-end (human-in-the-loop): o agente a
 * chama antes de gerar um gráfico amplo ou ambíguo, o grafo pausa, o usuário
 * aprova ou pede para esclarecer (`respond`) e o agente continua.
 */
export function useChartConfirmation() {
  useHumanInTheLoop({
    agentId: AGENT_ID,
    name: "confirm_chart_spec",
    description:
      "Ask the user to confirm (or reject) a proposed chart specification " +
      "before running it, when the request is broad or ambiguous (no " +
      "specific fields/filters, or spans the whole dataset).",
    parameters: z.object({
      reason: z
        .string()
        .describe("Why confirmation is needed, shown to the user."),
      chart_type: z.enum(["bar", "line", "pie"]).optional(),
      x_field: z.string().optional(),
      y_field: z.string().optional(),
      group_by: z.string().optional(),
      agg: z.string().optional(),
      filters: z.record(z.string(), z.unknown()).optional(),
      title: z.string().optional(),
    }),
    render: ({ args, status, respond }) => (
      <ChartSpecConfirmation
        args={args as ChartSpecArgs}
        status={status}
        respond={respond}
      />
    ),
  });
}
