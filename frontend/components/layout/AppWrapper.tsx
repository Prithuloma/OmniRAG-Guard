"use client";

import { AuthProvider, useAuth } from "@/context/AuthContext";
import Sidebar from "./Sidebar";
import SignIn from "../auth/SignIn";
import HistoryDrawer from "./HistoryDrawer";
import { Loader } from "lucide-react";

function InnerAppWrapper({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white font-sans">
        <div className="flex flex-col items-center gap-4">
          <Loader className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm text-slate-400">Loading your profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <SignIn />;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto bg-background text-foreground">
        {children}
      </main>
      <HistoryDrawer />
    </div>
  );
}

export default function AppWrapper({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <InnerAppWrapper>{children}</InnerAppWrapper>
    </AuthProvider>
  );
}
