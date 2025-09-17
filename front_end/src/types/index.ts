export interface User {
  id: string;
  username: string;
  email: string;
  is_admin: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  is_admin?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ChatSession {
  id: string;
  session_name: string;
  user_id: string;
  session_admin_id?: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  chunk_size: number;
  chunk_overlap: number;
  enable_internet_search: boolean;
  // Model configuration (non-sensitive fields only; api key is write-only)
  model_provider?: 'ollama' | 'openai' | 'groq' | null;
  model_name?: string | null;
  model_temperature?: number | null;
  model_max_output_tokens?: number | null;
  model_base_url?: string | null; // for Ollama
  document_count?: number;
}

// Payload for creating/updating a session (admin or session-admin)
export interface ModelConfigUpdate {
  model_provider?: 'ollama' | 'openai' | 'groq';
  model_name?: string;
  model_temperature?: number;
  model_max_output_tokens?: number;
  model_base_url?: string; // Ollama
  model_api_key?: string;  // write-only; used for OpenAI/Groq
}

export interface ChatThread {
  id: string;
  session_id: string;
  title?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionCreate {
  session_name: string;
  chunk_size?: number;
  chunk_overlap?: number;
  enable_internet_search?: boolean;
  session_admin_id?: string; // optional when created by global admin
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  session_id: string;
  uploaded_at: string;
  processed: boolean;
  page_count: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  user_id: string;
  message_type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  rag_strategy?: string;
}

export interface ChatHistory {
  messages: ChatMessage[];
}

export interface RAGConfig {
  strategy: 'naive' | 'chunking' | 'contextual' | 'multi_query';
  k: number;
  chunk_size?: number;
  chunk_overlap?: number;
}

export interface ChatRequest {
  message: string;
  session_id: string;
  thread_id?: string;
  rag_config?: RAGConfig;
  // If true, prioritize internet search results first (when session allows);
  // if false or omitted, internet search is used as last fallback.
  prefer_internet_first?: boolean;
}

export interface StreamResponse {
  content: string;
  is_complete: boolean;
  rag_strategy?: string;
}

export interface Analytics {
  users: number;
  sessions: number;
  documents: number;
  messages: number;
}

export interface MCPTool {
  id: string;
  session_id: string;
  name: string;
  tool_type: 'api' | 'python_function';
  api_url?: string;
  http_method?: string;
  function_code?: string;
  description?: string;
  params_docstring?: string;
  returns_docstring?: string;
  created_at: string;
  updated_at: string;
}