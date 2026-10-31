import { HttpAgent } from "@ag-ui/client";
import {
  CopilotKitIntelligence,
  CopilotRuntime,
  createCopilotRuntimeHandler,
} from "@copilotkit/runtime/v2";

// The IMDB movies-analysis agent: a Python LangGraph agent served over AG-UI
// by a standalone FastAPI process (agent/main.py, port 8123).
const imdbAgent = new HttpAgent({
  url: process.env.IMDB_AGENT_URL || "http://localhost:8123",
});

const runtime = new CopilotRuntime({
  agents: {
    imdb_agent: imdbAgent,
  },
  // Connects the runtime to CopilotKit Intelligence (AG-UI Streams / Rich
  // Threads, the Inspector, and Automatic Learning). The Python agent above
  // requires Intelligence: it has no SSE/in-memory runner fallback.
  intelligence: new CopilotKitIntelligence({
    apiKey: process.env.CPK_INTELLIGENCE_API_KEY!,
    // Assigns this agent's threads to the pre-created Learning container so
    // Automatic Learning can analyze them.
    getLearningContainerId: () => "imdb-movies-agent",
  }),
  // Local-dev placeholder identity: every visitor currently shares the
  // "local-user" thread history. Replace with a real verified session/token
  // lookup (see the Intelligence quickstart) before deploying with more than
  // one user.
  identifyUser: (request) => ({
    id: request.headers.get("x-user-id") ?? "local-user",
    name: request.headers.get("x-user-name") ?? "Local user",
  }),
});

const handler = createCopilotRuntimeHandler({
  runtime,
  basePath: "/api/copilotkit",
});

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
