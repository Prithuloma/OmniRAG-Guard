import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import AppWrapper from "@/components/layout/AppWrapper";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });

export const metadata: Metadata = {
  title: "OmniRAG-Guard",
  description: "Adaptive Multi-Modal RAG with Hallucination Verification",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${geist.variable} ${geistMono.variable} font-sans bg-background text-foreground antialiased`}>
        <AppWrapper>
          {children}
        </AppWrapper>
      </body>
    </html>
  );
}
