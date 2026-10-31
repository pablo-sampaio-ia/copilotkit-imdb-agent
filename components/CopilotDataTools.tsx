"use client";

import { useHumanInTheLoop, useRenderTool } from "@copilotkit/react-core/v2";
import { z } from "zod";
import { ChartRenderer } from "./generative-ui/ChartRenderer";
import { CodeAnalysisResult } from "./generative-ui/CodeAnalysisResult";
import {
  ChartSpecConfirmation,
  type ChartSpecArgs,
} from "./generative-ui/ChartSpecConfirmation";

const AGENT_ID = "imdb_agent";

/**
 * Wires the IMDB movies-analysis agent's tools into the chat UI:
 *
 * - `plot_chart` is a real backend tool (agent/tools.py) that returns
 *   structured chart JSON. `useRenderTool` renders that result as a real
 *   chart (see ChartRenderer) -- this is CopilotKit's "tool rendering"
 *   pattern for a tool the backend actually executes, as opposed to
 *   `useComponent`'s tool-based Generative UI, which registers a brand-new
 *   frontend-only tool with no backend handler.
 * - `run_python_analysis` is also a real backend tool (a sandboxed code-exec
 *   tool for ad-hoc analysis); its text/table output is rendered in a
 *   monospace result card.
 * - `confirm_chart_spec` is a frontend-only, LLM-initiated human-in-the-loop
 *   gate (`useHumanInTheLoop`): the agent calls it before running a broad or
 *   ambiguous chart request, and the user approves or asks to clarify before
 *   the agent proceeds to call plot_chart.
 */
export function CopilotDataTools() {
  useRenderTool({
    name: "plot_chart",
    parameters: z.object({
      chart_type: z.enum(["bar", "line", "pie"]),
      x_field: z.string(),
      y_field: z.string().optional(),
      group_by: z.string().optional(),
      agg: z.string().optional(),
      filters: z.record(z.string(), z.unknown()).optional(),
      title: z.string().optional(),
      top_n: z.number().optional(),
    }),
    render: ({ status, result }) => (
      <ChartRenderer status={status} result={result} />
    ),
  });

  useRenderTool({
    name: "run_python_analysis",
    parameters: z.object({
      code: z.string(),
    }),
    render: ({ parameters, status, result }) => (
      <CodeAnalysisResult
        code={parameters?.code}
        status={status}
        result={result}
      />
    ),
  });

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

  return null;
}
