export interface HistoryItem {
  documentId: string;
  filename: string;
  size: string;
  uploadDate: string;
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
    };
    
    // Add to the front of the list, filter out duplicates if any, and keep exactly last 10
    const filteredHistory = history.filter(
      (h) => h.documentId !== item.documentId
    );
    const updatedHistory = [newItem, ...filteredHistory].slice(0, 10);
    
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
