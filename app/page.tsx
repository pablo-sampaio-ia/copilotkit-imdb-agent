"use client";

import {
  CopilotSidebar,
  CopilotThreadsDrawer,
  useAgentContext,
} from "@copilotkit/react-core/v2";
import { Header } from "../components/Header";
import { Footer } from "../components/Footer";
import { CustomAssistantMessage } from "../components/AssistantMessage";
import { CopilotDataTools } from "../components/CopilotDataTools";
import { Suspense, useEffect, useState } from "react";
import { startCurrentTimeUpdates } from "../lib/current-time.mjs";

const EXAMPLE_PROMPTS = [
  "Show me a bar chart of average rating by genre",
  "Plot total worldwide gross by year for the last decade",
  "Which directors have the most Oscar wins in this dataset?",
  "Analyze the whole dataset for me",
];

function CurrentTimeContext() {
  const [currentTime, setCurrentTime] = useState(() =>
    new Date().toLocaleTimeString(),
  );

  useEffect(
    () =>
      startCurrentTimeUpdates(() => {
        setCurrentTime(new Date().toLocaleTimeString());
      }),
    [],
  );

  useAgentContext({
    description: "Current time",
    value: currentTime,
  });

  return null;
}

function HomeContent() {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <CurrentTimeContext />
      {/* Persistent thread switcher for the IMDB assistant's conversations;
          shares its active-thread state with the CopilotSidebar chat below
          via the CopilotChatConfigurationProvider that <CopilotKit> renders
          around the app in layout.tsx. */}
      <CopilotThreadsDrawer
        label="IMDB Movies Assistant threads"
        recentLabel="Recent Conversations"
      />
      <div className="flex flex-col flex-1">
        <CopilotDataTools />
        <Header />
        <main className="w-full max-w-3xl mx-auto py-10 px-4 sm:px-6 lg:px-8 flex-grow">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-2">
              Try asking the assistant
            </h2>
            <p className="text-sm text-gray-500 mb-4">
              Charts, stats, and ad-hoc analysis render right here in the chat
              on the right. A few things to try:
            </p>
            <ul className="space-y-2">
              {EXAMPLE_PROMPTS.map((prompt) => (
                <li
                  key={prompt}
                  className="text-sm text-gray-700 bg-gray-50 border border-gray-100 rounded-md px-3 py-2"
                >
                  {prompt}
                </li>
              ))}
            </ul>
          </div>
        </main>
        <Footer />
        <CopilotSidebar
          defaultOpen
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
    </div>
  );
}

export default function Home() {
  return (
    <Suspense
      fallback={
        <div
          className="min-h-screen bg-gray-50 flex items-center justify-center"
          role="status"
          aria-live="polite"
        >
          <div
            className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"
            aria-hidden="true"
          />
          <span className="sr-only">Loading...</span>
        </div>
      }
    >
      <HomeContent />
    </Suspense>
  );
}
