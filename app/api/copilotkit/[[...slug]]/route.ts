import { HttpAgent } from "@ag-ui/client";
import {
  CopilotKitIntelligence,
  CopilotRuntime,
  createCopilotRuntimeHandler,
} from "@copilotkit/runtime/v2";
import { agentUrl, intelligenceApiKey } from "../../../../lib/runtime-config";

// O agente de análise: um agente LangGraph em Python, servido por AG-UI em um
// processo FastAPI separado (agent/main.py). O runtime só repassa as
// mensagens e os eventos entre o navegador e ele.
const agents = { imdb_agent: new HttpAgent({ url: agentUrl }) };

// Dois modos de execução, decididos pela presença de CPK_INTELLIGENCE_API_KEY:
//
// 1. Com Intelligence: threads persistentes (AG-UI Streams), Inspector e
//    Automatic Learning, hospedados pelo CopilotKit na nuvem.
// 2. Sem Intelligence: modo SSE local, estado só em memória. Serve para
//    estudar o projeto sem conta; as conversas não persistem.
const runtime = intelligenceApiKey
  ? new CopilotRuntime({
      agents,
      intelligence: new CopilotKitIntelligence({
        apiKey: intelligenceApiKey,
        // Associa as threads deste agente ao container de Learning já criado.
        getLearningContainerId: () => "imdb-movies-agent",
      }),
      // Identidade provisória para desenvolvimento local: todos os visitantes
      // compartilham o histórico de "local-user". Troque por uma sessão
      // verificada antes de ter mais de um usuário.
      identifyUser: (request) => ({
        id: request.headers.get("x-user-id") ?? "local-user",
        name: request.headers.get("x-user-name") ?? "Local user",
      }),
    })
  : new CopilotRuntime({ agents });

console.log(
  `[imdb] CopilotKit runtime: ${
    intelligenceApiKey
      ? "Intelligence mode (persistent threads)"
      : "local SSE mode (no CPK_INTELLIGENCE_API_KEY; threads are not persisted)"
  }; agent at ${agentUrl}`,
);

const handler = createCopilotRuntimeHandler({
  runtime,
  basePath: "/api/copilotkit",
});

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
