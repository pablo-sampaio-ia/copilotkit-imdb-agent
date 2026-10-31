"use client";

import { useRenderTool } from "@copilotkit/react-core/v2";
import { z } from "zod";
import { CodeAnalysisResult } from "../generative-ui/CodeAnalysisResult";

/** Mostra o código, a saída e a imagem (se houver) de run_python_analysis. */
export function usePythonAnalysisTool() {
  useRenderTool({
    name: "run_python_analysis",
    parameters: z.object({ code: z.string() }),
    render: ({ parameters, status, result }) => (
      <CodeAnalysisResult
        code={parameters?.code}
        status={status}
        result={result}
      />
    ),
  });
}
