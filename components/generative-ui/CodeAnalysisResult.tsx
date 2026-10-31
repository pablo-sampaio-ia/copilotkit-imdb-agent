import React from "react";
import { AlertCircle, Loader, Terminal } from "lucide-react";

type CodeAnalysisResultProps = {
  code: string | undefined;
  status: "executing" | "inProgress" | "complete";
  result: string | undefined;
};

/**
 * Renders the `run_python_analysis` backend tool's call (the code it ran)
 * and its text/table result in a monospace card, since this tool returns
 * plain text rather than the structured chart JSON `ChartRenderer` expects.
 */
export function CodeAnalysisResult({
  code,
  status,
  result,
}: CodeAnalysisResultProps) {
  const isError = typeof result === "string" && result.startsWith("Error:");

  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <Terminal className="h-4 w-4 text-indigo-500" />
        <h3 className="text-sm font-medium">Ad-hoc analysis</h3>
      </div>

      {code && (
        <pre className="text-xs bg-gray-50 dark:bg-gray-900 rounded-md p-2 mb-2 overflow-x-auto">
          <code>{code}</code>
        </pre>
      )}

      {(status === "executing" || status === "inProgress") && (
        <div className="flex items-center gap-2 text-xs text-indigo-500">
          <Loader className="h-3 w-3 animate-spin" />
          <span>Running...</span>
        </div>
      )}

      {status === "complete" && result && (
        <pre
          className={`text-xs whitespace-pre-wrap overflow-x-auto rounded-md p-2 ${
            isError
              ? "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-300"
              : "bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200"
          }`}
        >
          {isError && (
            <span className="inline-flex items-center gap-1 font-medium">
              <AlertCircle className="h-3 w-3" /> Error
            </span>
          )}
          {"\n"}
          {result}
        </pre>
      )}

      {status === "complete" && !result && (
        <p className="text-sm text-gray-500">No output was returned.</p>
      )}
    </div>
  );
}
