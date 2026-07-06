import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/providers";

export const metadata: Metadata = {
  title: "AgentShadow — Discover. Govern. Protect.",
  description:
    "AgentShadow finds every AI agent across your code and runtime, scores its risk deterministically, and enforces governance policies.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
