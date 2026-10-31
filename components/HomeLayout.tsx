"use client";

import { CopilotSidebar, CopilotThreadsDrawer } from "@copilotkit/react-core/v2";
import { ChatSuggestions } from "./ChatSuggestions";
import { CopilotDataTools } from "./CopilotDataTools";
import { CustomAssistantMessage } from "./AssistantMessage";
import { Header } from "./Header";

type HomeLayoutProps = {
  /** A lista de conversas só existe com o CopilotKit Intelligence. */
  threadsEnabled: boolean;
};

/**
 * Layout em três áreas lado a lado:
 *   [threads] [painel central] [chat]
 * O chat (CopilotSidebar) é `position: fixed` e empurra o <body> com uma
 * margem à direita quando está aberto, por isso aqui só descrevemos as duas
 * primeiras áreas.
 */
export function HomeLayout({ threadsEnabled }: HomeLayoutProps) {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Estes dois só registram configuração; não desenham nada. */}
      <CopilotDataTools />
      <ChatSuggestions />

      {threadsEnabled && (
        <aside className="threads-column h-full shrink-0 border-r border-gray-200 bg-white">
          <CopilotThreadsDrawer
            label="IMDB Movies Assistant threads"
            recentLabel="Recent Conversations"
          />
        </aside>
      )}

      <div className="flex min-w-0 flex-1 flex-col overflow-y-auto">
        <Header />
        <main className="mx-auto w-full max-w-3xl flex-grow px-4 py-10 sm:px-6">
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-2 text-lg font-medium text-gray-900">
              How it works
            </h2>
            <p className="text-sm text-gray-500">
              Chat with the assistant in the panel on the right. Charts, stats
              and ad-hoc analyses are rendered inside the chat itself. Use the
              suggestions in the chat to get started
              {threadsEnabled
                ? ", or the conversation history on the left to resume an earlier analysis."
                : "."}
            </p>
            {!threadsEnabled && (
              <p className="mt-3 text-xs text-gray-400">
                Running without CopilotKit Intelligence: conversations are kept
                in memory only. Set CPK_INTELLIGENCE_API_KEY in .env for
                persistent threads and the Inspector.
              </p>
            )}
          </div>
        </main>
      </div>

      <CopilotSidebar
        defaultOpen
        // Largura fixa: sem ela o CopilotSidebar mede o próprio elemento e
        // pode colapsar para menos de 1px.
        width={480}
        messageView={{ assistantMessage: CustomAssistantMessage }}
        labels={{
          modalHeaderTitle: "IMDB Movies Assistant",
          welcomeMessageText:
            "Hello, I'm here to help you explore the IMDB top-movies-per-year dataset. Try asking for a chart by genre, year, rating, or box office.",
          chatInputPlaceholder:
            "Ask about movies, ratings, genres, or box office...",
        }}
      />
    </div>
  );
}
