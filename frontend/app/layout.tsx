import type { Metadata } from "next";
import { Raleway } from "next/font/google";
import "./globals.css";
import { ChatProvider } from "@/lib/context";

const raleway = Raleway({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Digital Capability Intelligence Platform",
  description: "Qwen3-235B · LangGraph · BPMN · Neo4j | Track 4 Autopilot Agent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${raleway.className}`} suppressHydrationWarning>
        <ChatProvider>
          <div className="min-h-screen bg-[#0e1117] dark:bg-[#0e1117] text-gray-100">{children}</div>
        </ChatProvider>
      </body>
    </html>
  );
}