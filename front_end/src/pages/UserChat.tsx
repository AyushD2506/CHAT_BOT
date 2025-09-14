import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import { ChatMessage, ChatSession, ChatRequest, RAGConfig, ChatThread } from '../types';

const UserChat: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeTab, setActiveTab] = useState<'select' | 'chat'>('select');
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
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

  // Load threads when a session is selected
  useEffect(() => {
    const loadThreads = async () => {
      if (!selectedSessionId) return;
      setError(null);
      try {
        const t = await api.chat.listThreads(selectedSessionId);
        setThreads(t);
        // Auto-select most recent thread, else none
        if (t.length > 0) {
          setSelectedThreadId(t[0].id);
        } else {
          setSelectedThreadId(null);
        }
      } catch (e: any) {
        setError(e?.message || 'Failed to load previous chats');
      }
    };
    loadThreads();
    setActiveTab('chat'); // Jump to chat tab by default when a session is chosen
    setMessages([]);
  }, [selectedSessionId]);

  // Load chat history for selected thread
  useEffect(() => {
    const loadHistory = async () => {
      if (!selectedSessionId) return;
      setLoadingHistory(true);
      setError(null);
      try {
        if (selectedThreadId) {
          const history = await api.chat.getThreadHistory(selectedSessionId, selectedThreadId);
          setMessages(history.messages);
        } else {
          // No thread yet: show empty state
          setMessages([]);
        }
      } catch (e: any) {
        setError(e?.message || 'Failed to load chat history');
      } finally {
        setLoadingHistory(false);
      }
    };
    loadHistory();
  }, [selectedSessionId, selectedThreadId]);

  const handleSend = async () => {
    if (!input.trim() || !selectedSessionId) return;

    const content = input.trim();
    setInput('');
    setSending(true);
    setError(null);

    // Ensure a thread exists before sending
    let threadId = selectedThreadId;
    try {
      if (!threadId) {
        const newThread = await api.chat.createThread(selectedSessionId);
        threadId = newThread.id;
        setSelectedThreadId(threadId);
        setThreads((prev) => [newThread, ...prev]);
      }
    } catch (e: any) {
      setSending(false);
      setError('Failed to create new chat');
      return;
    }

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
        thread_id: threadId!,
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
  };

  return (
    <div className="h-[calc(100vh-3.5rem)] flex">{/* minus header height (14 * 0.25rem) */}
      {/* Sessions Sidebar */}
      <div className="w-72 bg-[#202123] border-r border-black/20 p-4 overflow-y-auto text-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-100 tracking-wide uppercase">Chat Sessions</h2>
        </div>

        {loadingSessions ? (
          <div className="text-xs text-gray-400">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="text-xs text-gray-400">
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
                      ? 'bg-[#343541] border-white/10 text-gray-100'
                      : 'bg-transparent border-white/10 hover:bg-white/5 text-gray-200'
                  }`}
                >
                  <div className="font-medium truncate">{s.session_name}</div>
                  <div className="text-[10px] text-gray-400 mt-0.5">
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
        <div className="bg-[#343541] border-b border-black/20 p-4">
          <h3 className="text-sm font-medium text-gray-200">
            {selectedSessionId
              ? sessions.find((s) => s.id === selectedSessionId)?.session_name || 'Chat'
              : 'Select a session to start chatting'}
          </h3>
        </div>

        {/* Tabs and content */}
        <div className="flex-1 flex">
          {/* Left panel inside Chat: tabs for Select and Chat */}
          <div className="w-80 border-r border-black/20 bg-[#343541] flex flex-col">
            {/* Tabs */}
            <div className="flex border-b border-black/20">
              <button
                className={`flex-1 px-3 py-2 text-xs tracking-wide uppercase ${activeTab === 'select' ? 'border-b-2 border-white/20 text-gray-100' : 'text-gray-300'}`}
                onClick={() => setActiveTab('select')}
              >
                Session
              </button>
              <button
                className={`flex-1 px-3 py-2 text-xs tracking-wide uppercase ${activeTab === 'chat' ? 'border-b-2 border-white/20 text-gray-100' : 'text-gray-300'}`}
                onClick={() => setActiveTab('chat')}
              >
                Chat
              </button>
            </div>

            {/* Tab content */}
            {activeTab === 'select' ? (
              <div className="p-3 text-xs text-gray-300">
                <p>Select a session on the left sidebar.</p>
              </div>
            ) : (
              <div className="flex-1 p-3 overflow-y-auto">
                {/* New Chat */}
                <button
                  onClick={async () => {
                    if (!selectedSessionId) return;
                    try {
                      const t = await api.chat.createThread(selectedSessionId);
                      setThreads((prev) => [t, ...prev]);
                      setSelectedThreadId(t.id);
                    } catch (e) {
                      setError('Failed to create new chat');
                    }
                  }}
                  className="w-full mb-3 px-3 py-2 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                  disabled={!selectedSessionId}
                >
                  + New Chat
                </button>

                {/* Previous chats */}
                <div className="text-[10px] font-semibold text-gray-400 mb-2 uppercase tracking-wide">Previous Chats</div>
                {threads.length === 0 ? (
                  <div className="text-[10px] text-gray-400">No chats yet.</div>
                ) : (
                  <ul className="space-y-1">
                    {threads.map((t) => (
                      <li key={t.id}>
                        <button
                          onClick={() => setSelectedThreadId(t.id)}
                          className={`w-full text-left px-3 py-2 rounded-md text-xs ${
                            selectedThreadId === t.id ? 'bg-white/5 text-gray-100' : 'hover:bg-white/5 text-gray-300'
                          }`}
                          title={t.title || t.id}
                        >
                          <div className="truncate">{t.title || 'Untitled chat'}</div>
                          <div className="text-[10px] text-gray-400">{new Date(t.updated_at).toLocaleString()}</div>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          {/* Messages Area */}
          <div className="flex-1 p-6 bg-[#343541] overflow-y-auto">
            {loadingHistory ? (
              <div className="text-gray-300">Loading messages...</div>
            ) : !selectedSessionId ? (
              <div className="text-center text-gray-300 mt-8">
                <p className="text-lg mb-4">Welcome to RAG Chatbot!</p>
                <p className="text-sm">Start by selecting a session on the left.</p>
              </div>
            ) : messages.length === 0 ? (
              <div className="text-center text-gray-300 mt-8">
                <p className="text-sm">Start a new chat or select a previous chat.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {messages.map((m) => (
                  <div key={m.id} className={`flex ${m.message_type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div
                      className={`max-w-[75%] px-4 py-3 rounded-2xl ${
                        m.message_type === 'user'
                          ? 'bg-[#10a37f] text-white rounded-br-md'
                          : 'bg-[#444654] text-gray-100 rounded-bl-md'
                      }`}
                    >
                      <div className="whitespace-pre-wrap break-words text-sm leading-6">{m.content}</div>
                      {m.rag_strategy && m.message_type === 'assistant' && (
                        <div className="text-[10px] opacity-70 mt-1">RAG: {m.rag_strategy}</div>
                      )}
                    </div>
                  </div>
                ))}
                {sending && (
                  <div className="flex justify-start">
                    <div className="max-w-[75%] px-4 py-3 rounded-2xl bg-[#444654] text-gray-200 rounded-bl-md">
                      <div className="text-sm animate-pulse">Thinking...</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {error && (
              <div className="mt-3 text-sm text-red-400">{error}</div>
            )}
          </div>
        </div>

        {/* Chat Input */}
        <div className="bg-[#343541] border-t border-black/20 p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              placeholder={!selectedSessionId ? 'Select a session to begin' : !selectedThreadId ? 'Start a New Chat or pick one' : 'Type your message...'}
              className="flex-1 px-4 py-3 rounded-md bg-[#40414F] text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
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
              className="px-4 py-3 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:opacity-50"
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