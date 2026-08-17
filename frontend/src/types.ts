export type ServiceStatus = {
  status: string;
  graphstudio: string;
  llm: string;
  graphmart_uri?: string;
  detail?: string;
};

export type SavedQuery = {
  uri: string;
  title: string;
  description?: string;
  modified?: string;
  forced_limit?: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatSessionSummary = {
  id: string;
  title: string;
  preview?: string;
  updated_at?: string;
  message_count?: number;
};

export type ChatSession = ChatSessionSummary & {
  messages: ChatMessage[];
};

export type StreamEvent = {
  type: "status" | "chunk" | "error" | "done";
  content?: string;
  session_id?: string;
  session_title?: string;
};
