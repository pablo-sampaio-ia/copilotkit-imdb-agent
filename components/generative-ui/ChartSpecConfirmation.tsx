import React from "react";
import { CheckCircle, HelpCircle, XCircle } from "lucide-react";

export type ChartSpecArgs = {
  reason?: string;
  chart_type?: "bar" | "line" | "pie";
  x_field?: string;
  y_field?: string;
  group_by?: string;
  agg?: string;
  filters?: Record<string, unknown>;
  title?: string;
};

export type ChartSpecResponse =
  | { approved: true; spec: ChartSpecArgs }
  | { approved: false };

type ChartSpecConfirmationProps = {
  args: ChartSpecArgs;
  status: "executing" | "inProgress" | "complete";
  respond?: (response: ChartSpecResponse) => void;
};

/**
 * Human-in-the-loop quality gate: the agent calls the `confirm_chart_spec`
 * frontend tool (registered with `useHumanInTheLoop`) before running a broad
 * or ambiguous chart request. This card shows the proposed chart spec and
 * lets the user approve it as-is or reject it so the agent can ask follow-up
 * questions instead.
 */
export function ChartSpecConfirmation({
  args,
  status,
  respond,
}: ChartSpecConfirmationProps) {
  const alreadyAnswered = status === "complete";

  return (
    <div className="bg-amber-50 dark:bg-amber-950/30 p-3 rounded-lg border border-amber-200 dark:border-amber-800 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <HelpCircle className="h-4 w-4 text-amber-600" />
        <h3 className="text-sm font-medium">Confirm chart before running</h3>
      </div>

      {args.reason && (
        <p className="text-xs text-gray-600 dark:text-gray-300 mb-2">
          {args.reason}
        </p>
      )}

      <dl className="text-xs text-gray-700 dark:text-gray-200 grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 mb-3">
        <dt className="font-medium">Chart type</dt>
        <dd>{args.chart_type ?? "(agent's choice)"}</dd>
        <dt className="font-medium">X field</dt>
        <dd>{args.x_field ?? "(unspecified)"}</dd>
        <dt className="font-medium">Y field</dt>
        <dd>{args.y_field ?? "(agent's choice)"}</dd>
        {args.group_by && (
          <>
            <dt className="font-medium">Group by</dt>
            <dd>{args.group_by}</dd>
          </>
        )}
        {args.agg && (
          <>
            <dt className="font-medium">Aggregation</dt>
            <dd>{args.agg}</dd>
          </>
        )}
        {args.filters && Object.keys(args.filters).length > 0 && (
          <>
            <dt className="font-medium">Filters</dt>
            <dd>{JSON.stringify(args.filters)}</dd>
          </>
        )}
      </dl>

      {!alreadyAnswered && (
        <div className="flex gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-md bg-amber-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-amber-700"
            onClick={() => respond?.({ approved: true, spec: args })}
          >
            <CheckCircle className="h-3 w-3" />
            Looks good, run it
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-md border border-gray-300 px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-800"
            onClick={() => respond?.({ approved: false })}
          >
            <XCircle className="h-3 w-3" />
            Let me clarify instead
          </button>
        </div>
      )}

      {alreadyAnswered && (
        <p className="text-xs text-gray-500">Answered.</p>
      )}
    </div>
  );
}
