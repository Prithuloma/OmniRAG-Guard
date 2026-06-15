export interface HistoryItem {
  documentId: string;
  filename: string;
  size: string;
  uploadDate: string;
  pinned?: boolean;
  status?: "queued" | "uploading" | "done" | "error";
  chunks?: number;
  pages?: number;
}

const HISTORY_KEY_PREFIX = "omnirag_history_";

export function getHistory(userId: string): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const data = localStorage.getItem(`${HISTORY_KEY_PREFIX}${userId}`);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error("Failed to read upload history:", error);
    return [];
  }
}

export function addHistory(
  userId: string,
  item: Omit<HistoryItem, "uploadDate">
): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const history = getHistory(userId);
    const newItem: HistoryItem = {
      ...item,
      uploadDate: new Date().toISOString(),
      pinned: item.pinned ?? false,
      status: item.status ?? "done",
    };
    
    // Add to the front of the list, filter out duplicates if any
    const filteredHistory = history.filter(
      (h) => h.documentId !== item.documentId
    );
    const updatedHistory = [newItem, ...filteredHistory];
    
    // Evict oldest unpinned files if total length exceeds 20
    if (updatedHistory.length > 20) {
      const excess = updatedHistory.length - 20;
      let evictedCount = 0;
      
      for (let i = updatedHistory.length - 1; i >= 0; i--) {
        if (!updatedHistory[i].pinned) {
          updatedHistory.splice(i, 1);
          evictedCount++;
          if (evictedCount >= excess) {
            break;
          }
        }
      }
    }
    
    localStorage.setItem(
      `${HISTORY_KEY_PREFIX}${userId}`,
      JSON.stringify(updatedHistory)
    );
    return updatedHistory;
  } catch (error) {
    console.error("Failed to save upload history:", error);
    return [];
  }
}

export function togglePinHistory(userId: string, documentId: string): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const history = getHistory(userId);
    const updatedHistory = history.map((h) =>
      h.documentId === documentId ? { ...h, pinned: !h.pinned } : h
    );
    localStorage.setItem(
      `${HISTORY_KEY_PREFIX}${userId}`,
      JSON.stringify(updatedHistory)
    );
    return updatedHistory;
  } catch (error) {
    console.error("Failed to toggle pin:", error);
    return [];
  }
}

export function deleteFromHistory(userId: string, documentId: string): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const history = getHistory(userId);
    const updatedHistory = history.filter((h) => h.documentId !== documentId);
    localStorage.setItem(
      `${HISTORY_KEY_PREFIX}${userId}`,
      JSON.stringify(updatedHistory)
    );
    return updatedHistory;
  } catch (error) {
    console.error("Failed to delete from history:", error);
    return [];
  }
}

export function renameHistoryItem(
  userId: string,
  documentId: string,
  newFilename: string
): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const history = getHistory(userId);
    const updatedHistory = history.map((h) =>
      h.documentId === documentId ? { ...h, filename: newFilename } : h
    );
    localStorage.setItem(
      `${HISTORY_KEY_PREFIX}${userId}`,
      JSON.stringify(updatedHistory)
    );
    return updatedHistory;
  } catch (error) {
    console.error("Failed to rename history item:", error);
    return [];
  }
}
