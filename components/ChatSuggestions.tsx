"use client";

import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

/**
 * Sugestões clicáveis exibidas no chat (lista estática, sem chamar o LLM). Não renderiza nada por conta própria: só registra a configuração.
 */
export function ChatSuggestions() {
  useConfigureSuggestions({
    available: "always",
    suggestions: [
      {
        title: "Average rating by genre",
        message: "Show me a bar chart of average rating by genre",
      },
      {
        title: "Gross by year",
        message: "Plot total worldwide gross by year for the last decade",
      },
      {
        title: "Directors with most Oscars",
        message: "Which directors have the most Oscar wins in this dataset?",
      },
      {
        title: "Analyze everything",
        message: "Analyze the whole dataset for me",
      },
    ],
  });

  return null;
}
