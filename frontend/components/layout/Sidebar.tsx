"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  MessageSquare,
  Upload,
  Shield,
  LogOut,
  History,
  Plus,
  Pencil,
  Trash2,
  Check,
  X
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
  getConversations,
  renameConversation,
  deleteConversation,
  groupConversations,
  Conversation
} from "@/lib/conversations";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Chat", href: "/chat", icon: MessageSquare },
  { label: "Upload", href: "/upload", icon: Upload },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeChatId = searchParams.get("id");
  const { user, logout, setHistoryOpen } = useAuth();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [chatSearchTerm, setChatSearchTerm] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  const loadConversations = () => {
    const userId = user?.uid || "guest";
    setConversations(getConversations(userId));
  };

  useEffect(() => {
    loadConversations();
  }, [user, pathname, searchParams]);

  const handleRename = (id: string) => {
    const userId = user?.uid || "guest";
    if (editingTitle.trim()) {
      const updated = renameConversation(userId, id, editingTitle.trim());
      setConversations(updated);
    }
    setEditingId(null);
  };

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    const userId = user?.uid || "guest";
    if (confirm("Are you sure you want to delete this conversation?")) {
      const updated = deleteConversation(userId, id);
      setConversations(updated);
      if (activeChatId === id) {
        router.push("/chat");
      }
    }
  };

  const startRename = (id: string, title: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setEditingId(id);
    setEditingTitle(title);
  };

  // Filter conversations by search term
  const filteredConversations = conversations.filter(c =>
    c.title.toLowerCase().includes(chatSearchTerm.toLowerCase()) ||
    c.messages.some(m => m.content.toLowerCase().includes(chatSearchTerm.toLowerCase()))
  );

  const groups = groupConversations(filteredConversations);

  return (
    <aside style={{
      width: "240px",
      minHeight: "100vh",
      borderRight: "1px solid rgba(139, 92, 246, 0.2)",
      background: "rgba(10, 8, 20, 0.85)",
      backdropFilter: "blur(12px)",
      display: "flex",
      flexDirection: "column",
      position: "relative",
      zIndex: 10,
    }}>
      {/* Logo */}
      <div style={{
        padding: "20px 24px",
        borderBottom: "1px solid rgba(139, 92, 246, 0.2)",
        display: "flex",
        alignItems: "center",
        gap: "10px",
      }}>
        <Shield style={{ width: "20px", height: "20px", color: "#a78bfa" }} />
        <span style={{
          fontWeight: 600,
          fontSize: "14px",
          color: "#e2e0ff",
          letterSpacing: "0.05em",
        }}>OmniRAG-Guard</span>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "16px 12px", display: "flex", flexDirection: "column", gap: "4px" }}>
        {navItems.map(({ label, href, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href} style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              padding: "10px 14px",
              borderRadius: "8px",
              fontSize: "13px",
              textDecoration: "none",
              transition: "all 0.2s",
              background: active ? "rgba(139, 92, 246, 0.15)" : "transparent",
              color: active ? "#a78bfa" : "rgba(200, 195, 255, 0.6)",
              boxShadow: active ? "inset 0 0 20px rgba(139, 92, 246, 0.1), 0 0 10px rgba(139, 92, 246, 0.1)" : "none",
              border: active ? "1px solid rgba(139, 92, 246, 0.3)" : "1px solid transparent",
            }}>
              <Icon style={{ width: "16px", height: "16px" }} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom glow */}
      <div style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        height: "200px",
        background: "radial-gradient(ellipse at 50% 100%, rgba(139, 92, 246, 0.15) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />
    </aside>
  );
}