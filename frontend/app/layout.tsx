import type { Metadata } from "next";
import { Raleway } from "next/font/google";
import "./globals.css";
import { ChatProvider } from "@/lib/context";

const raleway = Raleway({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "UiPath EA Orchestrator",
  description: "BPMN Process Integration for Enterprise Architecture",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${raleway.className} bg-[#0e1117] text-gray-100`}>
        <ChatProvider>
          <div className="min-h-screen">{children}</div>
        </ChatProvider>
      </body>
    </html>
  );
}
