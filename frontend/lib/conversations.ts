export interface Evidence {
  id: string;
  source: string;
  chunk: string;
  relevance: number;
  document_id?: string;
  page_number?: number;
}

export interface ClaimCitation {
  document_id: string;
  page_number: number;
  source_index: number;
}

export interface ClaimVerification {
  text: string;
  grounding_score: number;
  status: "grounded" | "partially_grounded" | "ungrounded";
  citations: ClaimCitation[];
}

export interface ConflictDetail {
  source_a: string;
  source_b: string;
  page_a: number;
  page_b: number;
  description: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence?: number;
  grounded?: boolean;
  evidence?: Evidence[];
  loading?: boolean;
  timestamp?: string;
  groundingScore?: number;
  evidenceScore?: number;
  latencyMs?: number;
  searchTimeMs?: number;
  rerankTimeMs?: number;
  verificationReason?: string;
  streaming?: boolean;
  retrievalTimeMs?: number;
  generationTimeMs?: number;
  verificationTimeMs?: number;
  embeddingModel?: string;
  llmModel?: string;
  semanticSimilarity?: number;
  lexicalOverlap?: number;
  consensusScore?: number;
  claims?: ClaimVerification[];
  conflicts?: ConflictDetail[];
  selfCorrectionTriggered?: boolean;
  refinementTimeMs?: number;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: string;
}

const CONVERSATIONS_KEY_PREFIX = "omnirag_conversations_";

export function getConversations(userId: string): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const data = localStorage.getItem(`${CONVERSATIONS_KEY_PREFIX}${userId}`);
    if (!data) return [];
    const parsed = JSON.parse(data) as Conversation[];
    // Sort by updatedAt descending
    return parsed.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
  } catch (error) {
    console.error("Failed to read conversations:", error);
    return [];
  }
}

export function saveConversation(userId: string, conversation: Conversation): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const list = getConversations(userId);
    const existingIndex = list.findIndex((c) => c.id === conversation.id);
    const updatedConv = {
      ...conversation,
      updatedAt: new Date().toISOString(),
    };
    if (existingIndex > -1) {
      list[existingIndex] = updatedConv;
    } else {
      list.push(updatedConv);
    }
    localStorage.setItem(
      `${CONVERSATIONS_KEY_PREFIX}${userId}`,
      JSON.stringify(list)
    );
    return getConversations(userId);
  } catch (error) {
    console.error("Failed to save conversation:", error);
    return [];
  }
}

export function deleteConversation(userId: string, conversationId: string): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const list = getConversations(userId);
    const filtered = list.filter((c) => c.id !== conversationId);
    localStorage.setItem(
      `${CONVERSATIONS_KEY_PREFIX}${userId}`,
      JSON.stringify(filtered)
    );
    return filtered;
  } catch (error) {
    console.error("Failed to delete conversation:", error);
    return [];
  }
}

export function renameConversation(
  userId: string,
  conversationId: string,
  newTitle: string
): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const list = getConversations(userId);
    const updated = list.map((c) =>
      c.id === conversationId ? { ...c, title: newTitle, updatedAt: new Date().toISOString() } : c
    );
    localStorage.setItem(
      `${CONVERSATIONS_KEY_PREFIX}${userId}`,
      JSON.stringify(updated)
    );
    return updated;
  } catch (error) {
    console.error("Failed to rename conversation:", error);
    return [];
  }
}

export interface ConversationGroup {
  label: string;
  conversations: Conversation[];
}

export function groupConversations(conversations: Conversation[]): ConversationGroup[] {
  const groups: { [key: string]: Conversation[] } = {
    Today: [],
    Yesterday: [],
    Earlier: [],
  };

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  yesterday.setHours(0, 0, 0, 0);

  conversations.forEach((c) => {
    const date = new Date(c.updatedAt);
    if (date >= today) {
      groups.Today.push(c);
    } else if (date >= yesterday) {
      groups.Yesterday.push(c);
    } else {
      groups.Earlier.push(c);
    }
  });

  return [
    { label: "Today", conversations: groups.Today },
    { label: "Yesterday", conversations: groups.Yesterday },
    { label: "Earlier", conversations: groups.Earlier },
  ].filter((g) => g.conversations.length > 0);
}
