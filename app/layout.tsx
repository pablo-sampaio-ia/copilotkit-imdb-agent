import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { CopilotKit } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "IMDB Movies Analysis",
  description:
    "AI-powered assistant for exploring the IMDB top-movies-per-year dataset",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <CopilotKit
          runtimeUrl="/api/copilotkit"
          agent="imdb_agent"
          showDevConsole={false}
          useSingleEndpoint={false}
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
