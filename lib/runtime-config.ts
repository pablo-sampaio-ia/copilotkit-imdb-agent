// Configuração do lado do servidor, lida das variáveis de ambiente (.env).
// Usada pela rota do runtime e pela página; nunca importar em componentes
// "use client" (as variáveis não existem no navegador).

/** Onde roda o agente Python (agent/main.py). */
export const agentUrl = process.env.IMDB_AGENT_URL || "http://localhost:8123";

/**
 * Chave do CopilotKit Intelligence (serviço gerenciado na nuvem). Com ela, o
 * app ganha threads persistentes e o Inspector. Sem ela, o runtime funciona
 * localmente em modo SSE com estado em memória: o chat funciona, mas a lista
 * de conversas e o histórico somem ao recarregar.
 */
export const intelligenceApiKey =
  process.env.CPK_INTELLIGENCE_API_KEY?.trim() || undefined;
