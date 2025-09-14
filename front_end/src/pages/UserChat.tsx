import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import { ChatMessage, ChatSession, ChatRequest, RAGConfig } from '../types';

const UserChat: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>('');
  const [loadingSessions, setLoadingSessions] = useState<boolean>(false);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [sending, setSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Optional: default RAG config (can be extended with UI later)
  const defaultRagConfig: RAGConfig = useMemo(() => ({
    strategy: 'contextual',
    k: 5,
  }), []);

  // Load user's chat sessions on mount
  useEffect(() => {
    const loadSessions = async () => {
      setLoadingSessions(true);
      setError(null);
      try {
        const list = await api.chat.listUserSessions();
        setSessions(list);
        // Auto-select the most recent session if available
        if (list.length > 0) {
          setSelectedSessionId(list[0].id);
        }
      } catch (e: any) {
        setError(e?.message || 'Failed to load sessions');
      } finally {
        setLoadingSessions(false);
      }
    };
    loadSessions();
  }, []);

  // Load chat history when a session is selected
  useEffect(() => {
    const loadHistory = async () => {
      if (!selectedSessionId) return;
      setLoadingHistory(true);
      setError(null);
      try {
        const history = await api.chat.getChatHistory(selectedSessionId);
        setMessages(history.messages);
      } catch (e: any) {
        setError(e?.message || 'Failed to load chat history');
      } finally {
        setLoadingHistory(false);
      }
    };
    loadHistory();
  }, [selectedSessionId]);

  const handleSend = async () => {
    if (!input.trim() || !selectedSessionId) return;

    const content = input.trim();
    setInput('');
    setSending(true);
    setError(null);

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: selectedSessionId,
      user_id: 'me',
      message_type: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const payload: ChatRequest = {
        message: content,
        session_id: selectedSessionId,
        rag_config: defaultRagConfig,
      };

      const assistantMsg = await api.chat.sendMessage(payload);
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const handleSelectSession = (id: string) => {
    if (id === selectedSessionId) return;
    setSelectedSessionId(id);
    setMessages([]);
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex">{/* minus header height */}
      {/* Sessions Sidebar */}
      <div className="w-72 bg-white border-r border-gray-200 p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Chat Sessions</h2>
        </div>

        {loadingSessions ? (
          <div className="text-sm text-gray-600">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="text-sm text-gray-600">
            No sessions available. Ask admin to create a session and upload documents.
          </div>
        ) : (
          <ul className="space-y-2">
            {sessions.map((s) => (
              <li key={s.id}>
                <button
                  onClick={() => handleSelectSession(s.id)}
                  className={`w-full text-left px-3 py-2 rounded-md border ${
                    selectedSessionId === s.id
                      ? 'bg-blue-50 border-blue-300 text-blue-800'
                      : 'bg-white border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium truncate">{s.session_name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    Docs: {s.document_count ?? 0}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <h3 className="text-lg font-medium text-gray-900">
            {selectedSessionId
              ? sessions.find((s) => s.id === selectedSessionId)?.session_name || 'Chat'
              : 'Select a session to start chatting'}
          </h3>
        </div>

        {/* Messages Area */}
        <div className="flex-1 p-4 bg-gray-50 overflow-y-auto">
          {loadingHistory ? (
            <div className="text-gray-600">Loading messages...</div>
          ) : messages.length === 0 ? (
            <div className="text-center text-gray-600 mt-8">
              <p className="text-lg mb-4">Welcome to RAG Chatbot!</p>
              <p className="text-sm">Start by selecting a session on the left.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {messages.map((m) => (
                <div key={m.id} className={`flex ${m.message_type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[75%] px-3 py-2 rounded-lg shadow-sm ${
                      m.message_type === 'user'
                        ? 'bg-blue-600 text-white rounded-br-none'
                        : 'bg-white text-gray-900 border border-gray-200 rounded-bl-none'
                    }`}
                  >
                    <div className="whitespace-pre-wrap break-words text-sm">{m.content}</div>
                    {m.rag_strategy && m.message_type === 'assistant' && (
                      <div className="text-[10px] opacity-70 mt-1">RAG: {m.rag_strategy}</div>
                    )}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="max-w-[75%] px-3 py-2 rounded-lg border border-gray-200 bg-white text-gray-900 rounded-bl-none">
                    <div className="text-sm animate-pulse">Thinking...</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="mt-3 text-sm text-red-600">{error}</div>
          )}
        </div>

        {/* Chat Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              placeholder={selectedSessionId ? 'Type your message...' : 'Select a session to begin'}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={!selectedSessionId || sending}
            />
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              onClick={handleSend}
              disabled={!selectedSessionId || sending || input.trim().length === 0}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserChat;