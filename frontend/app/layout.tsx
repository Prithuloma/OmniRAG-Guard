import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Sidebar from "@/components/layout/Sidebar";
import ParticleBackground from "@/components/layout/ParticleBackground";
import "./globals.css";
import CustomCursor from "@/components/layout/CustomCursor";

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
        <ParticleBackground />
        <CustomCursor />

        <div style={{ position: "relative", zIndex: 1, display: "flex", minHeight: "100vh" }}>
          <Sidebar />
          <main className="flex-1 overflow-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
