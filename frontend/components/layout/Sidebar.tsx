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
    <aside className="w-60 min-h-screen border-r border-border bg-slate-950 flex flex-col justify-between font-sans transition-all duration-300">
      <div className="flex flex-col flex-1 min-h-0">
        <div className="px-6 py-5 flex items-center gap-2.5 border-b border-border flex-shrink-0">
          <div className="p-1.5 rounded-lg bg-primary/10 text-primary border border-primary/20">
            <Shield className="w-4 h-4" />
          </div>
          <span className="font-bold text-xs tracking-wider uppercase bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
            OmniRAG-Guard
          </span>
        </div>

        {/* Navigation Section */}
        <nav className="px-3 py-4 space-y-1 flex-shrink-0 border-b border-border bg-slate-900/10">
          {navItems.map(({ label, href, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all duration-200
                ${pathname === href && !activeChatId
                  ? "bg-primary text-primary-foreground shadow-md shadow-primary/15"
                  : "text-muted-foreground hover:text-foreground hover:bg-slate-900/60 border border-transparent hover:border-border/30"
                }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
          <button
            onClick={() => setHistoryOpen(true)}
            className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-slate-900/60 border border-transparent hover:border-border/30 w-full text-left transition-all duration-200 cursor-pointer"
          >
            <History className="w-4 h-4" />
            <span>Files History</span>
          </button>
        </nav>

        {/* Chat History Section */}
        <div className="flex-1 overflow-y-auto px-3 py-4 flex flex-col min-h-0">
          <div className="flex items-center justify-between px-3 mb-2 flex-shrink-0">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60">
              Conversations
            </span>
            <Link
              href="/chat"
              className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-slate-900 border border-transparent hover:border-border/40 transition-all"
              title="New Chat"
            >
              <Plus className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Conversations Search Bar */}
          <div className="px-2 mb-4 flex-shrink-0">
            <div className="relative">
              <input
                type="text"
                placeholder="Search chats..."
                value={chatSearchTerm}
                onChange={(e) => setChatSearchTerm(e.target.value)}
                className="w-full pl-7 pr-3 py-1 bg-slate-900/40 text-[11px] text-white border border-border/60 rounded-lg focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-muted-foreground/50 transition-all"
              />
              <svg
                className="absolute left-2.5 top-2 w-3 h-3 text-muted-foreground/60"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          <div className="space-y-4 flex-1 overflow-y-auto pr-1">
            {groups.length === 0 ? (
              <p className="text-[11px] text-muted-foreground/55 px-3 py-2 italic">
                {chatSearchTerm ? "No matching chats" : "No chats yet"}
              </p>
            ) : (
              groups.map((group) => (
                <div key={group.label} className="space-y-1">
                  <div className="text-[9px] font-bold text-muted-foreground/45 px-3 uppercase tracking-wider">
                    {group.label}
                  </div>
                  <div className="space-y-[2px]">
                    {group.conversations.map((conv) => {
                      const isActive = activeChatId === conv.id;
                      const isEditing = editingId === conv.id;

                      return (
                        <div
                          key={conv.id}
                          className={`group/item relative flex items-center rounded-xl transition-all duration-150 border border-transparent
                            ${isActive
                              ? "bg-slate-900 text-foreground border-border/50 shadow-inner"
                              : "text-muted-foreground hover:text-foreground hover:bg-slate-900/40"
                            }`}
                        >
                          {isEditing ? (
                            <div className="flex items-center gap-1 w-full px-2 py-1">
                              <input
                                type="text"
                                value={editingTitle}
                                onChange={(e) => setEditingTitle(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") handleRename(conv.id);
                                  if (e.key === "Escape") setEditingId(null);
                                }}
                                onBlur={() => handleRename(conv.id)}
                                className="flex-1 bg-slate-950 text-foreground border border-border rounded px-1.5 py-0.5 text-[11px] focus:outline-none focus:ring-1 focus:ring-primary"
                                autoFocus
                              />
                              <button
                                onClick={() => handleRename(conv.id)}
                                className="p-0.5 text-green-500 hover:bg-slate-800 rounded"
                              >
                                <Check className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="p-0.5 text-red-500 hover:bg-slate-800 rounded"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          ) : (
                            <div className="flex-1 flex items-center justify-between min-w-0 relative">
                              <Link
                                href={`/chat?id=${conv.id}`}
                                className="flex-1 truncate pr-16 pl-3 py-2 text-[11px] font-medium"
                              >
                                {conv.title || "Untitled Chat"}
                              </Link>
                              <div className={`absolute right-1 opacity-0 group-hover/item:opacity-100 flex items-center gap-0.5 pl-2 transition-opacity duration-150 rounded-lg
                                ${isActive ? "bg-slate-900" : "bg-gradient-to-l from-[#0e131f] via-[#0e131f] to-transparent"}`}
                              >
                                <button
                                  onClick={(e) => startRename(conv.id, conv.title, e)}
                                  className="p-1 text-muted-foreground/75 hover:text-foreground hover:bg-slate-800 rounded transition-colors"
                                  title="Rename"
                                >
                                  <Pencil className="w-3 h-3" />
                                </button>
                                <button
                                  onClick={(e) => handleDelete(conv.id, e)}
                                  className="p-1 text-muted-foreground/75 hover:text-destructive hover:bg-slate-800 rounded transition-colors"
                                  title="Delete"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {user && (
        <div className="p-4 border-t border-border flex flex-col gap-3 flex-shrink-0 bg-slate-900/20">
          <div className="flex items-center gap-3">
            {user.photoURL ? (
              <img
                src={user.photoURL}
                alt={user.displayName || "User"}
                className="w-8 h-8 rounded-full border border-border shadow"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold border border-primary/20 shadow">
                {user.displayName ? user.displayName.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase() : (user.email ? user.email.slice(0,2).toUpperCase() : "U")}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold truncate text-foreground">
                {user.displayName || user.email?.split("@")[0] || "User"}
              </p>
              <p className="text-[10px] text-muted-foreground truncate leading-normal">
                {user.email}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center justify-center gap-2 w-full px-3 py-2 rounded-xl border border-border/80 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/20 text-muted-foreground text-xs font-semibold transition-all duration-200 cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      )}
    </aside>
  );
}