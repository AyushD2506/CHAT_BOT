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
  created_at: string;
  updated_at: string;
  is_active: boolean;
  chunk_size: number;
  chunk_overlap: number;
  document_count?: number;
}

export interface ChatSessionCreate {
  session_name: string;
  chunk_size?: number;
  chunk_overlap?: number;
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
  rag_config?: RAGConfig;
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