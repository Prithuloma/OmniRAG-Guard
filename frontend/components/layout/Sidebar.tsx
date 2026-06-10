"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MessageSquare, Upload, Shield, LogOut, History } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Chat", href: "/chat", icon: MessageSquare },
  { label: "Upload", href: "/upload", icon: Upload },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout, setHistoryOpen } = useAuth();

  return (
    <aside className="w-60 min-h-screen border-r border-border bg-card flex flex-col justify-between">
      <div>
        <div className="px-6 py-5 flex items-center gap-2 border-b border-border">
          <Shield className="w-5 h-5 text-primary" />
          <span className="font-semibold text-sm tracking-wide">OmniRAG-Guard</span>
        </div>
        <nav className="px-3 py-4 space-y-1">
          {navItems.map(({ label, href, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors
                ${pathname === href
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
                }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
          <button
            onClick={() => setHistoryOpen(true)}
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-accent w-full text-left transition-colors cursor-pointer"
          >
            <History className="w-4 h-4" />
            <span>History</span>
          </button>
        </nav>
      </div>

      {user && (
        <div className="p-4 border-t border-border flex flex-col gap-3">
          <div className="flex items-center gap-3">
            {user.photoURL ? (
              <img
                src={user.photoURL}
                alt={user.displayName || "User"}
                className="w-9 h-9 rounded-full border border-border"
              />
            ) : (
              <div className="w-9 h-9 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold border border-primary/20">
                {user.displayName ? user.displayName.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase() : "U"}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate text-foreground">
                {user.displayName || "Authenticated User"}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user.email}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center justify-center gap-2 w-full px-3 py-2 rounded-md border border-border hover:bg-destructive/10 hover:text-destructive hover:border-destructive/20 text-muted-foreground text-sm transition-all duration-200"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      )}
    </aside>
  );
}