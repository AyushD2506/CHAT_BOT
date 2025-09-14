import axios from 'axios';
import {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  User,
  ChatSession,
  ChatSessionCreate,
  Document,
  ChatMessage,
  ChatHistory,
  ChatRequest,
  Analytics,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Auth endpoints
  auth: {
    login: async (credentials: LoginRequest): Promise<AuthResponse> => {
      const response = await apiClient.post('/auth/login', credentials);
      return response.data;
    },

    register: async (userData: RegisterRequest): Promise<User> => {
      const response = await apiClient.post('/auth/register', userData);
      return response.data;
    },

    me: async (): Promise<User> => {
      const response = await apiClient.get('/auth/me');
      return response.data;
    },

    listUsers: async (): Promise<User[]> => {
      const response = await apiClient.get('/auth/users');
      return response.data;
    },

    deleteUser: async (userId: string): Promise<void> => {
      await apiClient.delete(`/auth/users/${userId}`);
    },
  },

  // Admin endpoints
  admin: {
    // Sessions
    createSession: async (sessionData: ChatSessionCreate): Promise<ChatSession> => {
      const response = await apiClient.post('/admin/sessions', sessionData);
      return response.data;
    },

    listAllSessions: async (): Promise<ChatSession[]> => {
      const response = await apiClient.get('/admin/sessions');
      return response.data;
    },

    getSession: async (sessionId: string): Promise<ChatSession> => {
      const response = await apiClient.get(`/admin/sessions/${sessionId}`);
      return response.data;
    },

    updateSession: async (sessionId: string, updates: Partial<ChatSessionCreate>): Promise<ChatSession> => {
      const response = await apiClient.put(`/admin/sessions/${sessionId}`, updates);
      return response.data;
    },

    deleteSession: async (sessionId: string): Promise<void> => {
      await apiClient.delete(`/admin/sessions/${sessionId}`);
    },

    // Documents
    uploadDocument: async (sessionId: string, file: File): Promise<Document> => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post(`/admin/sessions/${sessionId}/documents`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },

    listSessionDocuments: async (sessionId: string): Promise<Document[]> => {
      const response = await apiClient.get(`/admin/sessions/${sessionId}/documents`);
      return response.data;
    },

    deleteDocument: async (documentId: string): Promise<void> => {
      await apiClient.delete(`/admin/documents/${documentId}`);
    },

    // Analytics
    getAnalytics: async (): Promise<Analytics> => {
      const response = await apiClient.get('/admin/analytics');
      return response.data;
    },
  },

  // Chat endpoints
  chat: {
    listUserSessions: async (): Promise<ChatSession[]> => {
      const response = await apiClient.get('/chat/sessions');
      return response.data;
    },

    getChatHistory: async (sessionId: string): Promise<ChatHistory> => {
      const response = await apiClient.get(`/chat/sessions/${sessionId}/history`);
      return response.data;
    },

    sendMessage: async (chatRequest: ChatRequest): Promise<ChatMessage> => {
      const response = await apiClient.post('/chat/message', chatRequest);
      return response.data;
    },

    streamMessage: async (chatRequest: ChatRequest): Promise<ReadableStream> => {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(chatRequest),
      });

      if (!response.body) {
        throw new Error('No response body');
      }

      return response.body;
    },

    listSessionDocuments: async (sessionId: string): Promise<Document[]> => {
      const response = await apiClient.get(`/chat/sessions/${sessionId}/documents`);
      return response.data;
    },

    deleteMessage: async (messageId: string): Promise<void> => {
      await apiClient.delete(`/chat/messages/${messageId}`);
    },
  },

  // Documents endpoints
  documents: {
    listUserDocuments: async (): Promise<Document[]> => {
      const response = await apiClient.get('/documents/');
      return response.data;
    },

    getDocument: async (documentId: string): Promise<Document> => {
      const response = await apiClient.get(`/documents/${documentId}`);
      return response.data;
    },
  },
};