import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ChatSession, Document, Analytics, User } from '../types';
import RowActionMenu from '../components/RowActionMenu';
import StatCard from '../components/StatCard';

const AdminDashboard: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedSessionAdminId, setSelectedSessionAdminId] = useState<string>('');
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // New states for session drill-down
  const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null);
  const [sessionDocuments, setSessionDocuments] = useState<Record<string, Document[]>>({});
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  // MCP tools modal state
  const [showToolsModal, setShowToolsModal] = useState(false);
  const [manageToolsSessionId, setManageToolsSessionId] = useState<string | null>(null);
  const [tools, setTools] = useState<import('../types').MCPTool[]>([]);
  const [toolForm, setToolForm] = useState<{ id?: string; name: string; tool_type: 'api' | 'python_function'; api_url?: string; http_method?: string; function_code?: string; description?: string; params_docstring?: string; returns_docstring?: string }>({ name: '', tool_type: 'api', http_method: 'GET' });
  const [toolMode, setToolMode] = useState<'list' | 'create' | 'edit'>('list');

  // Form states
  const [sessionName, setSessionName] = useState('');
  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(200);
  const [enableInternetSearch, setEnableInternetSearch] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Load data on component mount
  useEffect(() => {
    loadDashboardData();
  }, []);

  // Load users list lazily when opening Create Session modal
  useEffect(() => {
    if (showCreateModal) {
      api.auth
        .listUsers()
        .then(setUsers)
        .catch(() => setError('Failed to load users'));
    }
  }, [showCreateModal]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [sessionsData, analyticsData] = await Promise.all([
        api.admin.listAllSessions(),
        api.admin.getAnalytics()
      ]);
      setSessions(sessionsData);
      setAnalytics(analyticsData);
    } catch (err: any) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const newSession = await api.admin.createSession({
        session_name: sessionName,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
        enable_internet_search: enableInternetSearch,
        session_admin_id: selectedSessionAdminId || undefined,
      });
      
      setSessions(prev => [newSession, ...prev]);
      setShowCreateModal(false);
      setSessionName('');
      setChunkSize(1000);
      setChunkOverlap(200);
      setEnableInternetSearch(false);
      setSuccess('Session created successfully!');
      
      // Reload analytics
      const analyticsData = await api.admin.getAnalytics();
      setAnalytics(analyticsData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create session');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !selectedSession) return;

    setLoading(true);
    setError('');

    try {
      const doc = await api.admin.uploadDocument(selectedSession, uploadFile);
      setShowUploadModal(false);
      setUploadFile(null);
      setSuccess('Document uploaded successfully!');

      // Update session documents if expanded matches
      setSessionDocuments(prev => ({
        ...prev,
        [selectedSession]: [doc, ...(prev[selectedSession] || [])]
      }));

      // Update sessions list count
      setSessions(prev => prev.map(s => s.id === selectedSession ? { ...s, document_count: (s.document_count || 0) + 1 } : s));

      setSelectedSession('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!window.confirm('Are you sure you want to delete this session? This will delete all associated documents and messages.')) {
      return;
    }

    setLoading(true);
    try {
      await api.admin.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      setSuccess('Session deleted successfully!');
      
      // Reload analytics
      const analyticsData = await api.admin.getAnalytics();
      setAnalytics(analyticsData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete session');
    } finally {
      setLoading(false);
    }
  };

  // Clear messages after 3 seconds
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError('');
        setSuccess('');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  if (loading && !sessions.length) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            disabled={loading}
          >
            <span>+ Create Session</span>
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-white shadow-sm hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
            disabled={loading || sessions.length === 0}
          >
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded-md">
          {success}
        </div>
      )}

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard label="Users" value={analytics.users} kind="users" />
          <StatCard label="Sessions" value={analytics.sessions} kind="sessions" />
          <StatCard label="Documents" value={analytics.documents} kind="documents" />
          <StatCard label="Messages" value={analytics.messages} kind="messages" />
        </div>
      )}

      {/* Sessions List */}
      <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-100">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Chat Sessions</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Session Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Documents
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Chunk Settings
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Internet Search
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {sessions.map((session) => (
                <tr key={session.id} className="hover:bg-gray-50/60">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {session.session_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      ID: {session.id.substring(0, 8)}...
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {session.document_count || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    Size: {session.chunk_size}<br />
                    Overlap: {session.chunk_overlap}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      session.enable_internet_search 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {session.enable_internet_search ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(session.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      session.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {session.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <RowActionMenu
                      disabled={loading}
                      isExpanded={expandedSessionId === session.id}
                      onToggleExpand={async () => {
                        const nextId = expandedSessionId === session.id ? null : session.id;
                        setExpandedSessionId(nextId);
                        setSelectedDocumentId(null);
                        setPdfUrl(null);
                        if (nextId) {
                          try {
                            const docs = await api.admin.listSessionDocuments(session.id);
                            setSessionDocuments(prev => ({ ...prev, [session.id]: docs }));
                          } catch (err) {
                            setError('Failed to load session documents');
                          }
                        }
                      }}
                      isActive={session.is_active}
                      onToggleActive={async () => {
                        try {
                          const updated = await api.admin.updateSession(session.id, { is_active: !session.is_active });
                          setSessions(prev => prev.map(s => s.id === session.id ? { ...s, is_active: updated.is_active } : s));
                          setSuccess(`Session ${!session.is_active ? 'activated' : 'disabled'} successfully`);
                        } catch (err: any) {
                          setError(err.response?.data?.detail || 'Failed to update session status');
                        }
                      }}
                      isSearchEnabled={session.enable_internet_search}
                      onToggleSearch={async () => {
                        try {
                          await api.admin.updateSession(session.id, {
                            enable_internet_search: !session.enable_internet_search,
                          });
                          setSessions(prev => prev.map(s =>
                            s.id === session.id
                              ? { ...s, enable_internet_search: !s.enable_internet_search }
                              : s
                          ));
                          setSuccess(`Internet search ${!session.enable_internet_search ? 'enabled' : 'disabled'} for session`);
                        } catch (err: any) {
                          setError(err.response?.data?.detail || 'Failed to update internet search setting');
                        }
                      }}
                      onUploadPDF={() => {
                        setSelectedSession(session.id);
                        setShowUploadModal(true);
                      }}
                      onManageTools={async () => {
                        setExpandedSessionId(session.id);
                        setManageToolsSessionId(session.id);
                        setShowToolsModal(true);
                        try {
                          const data = await api.admin.listMcpTools(session.id);
                          setTools(data);
                        } catch {
                          setError('Failed to load tools');
                        }
                      }}
                      onDelete={() => handleDeleteSession(session.id)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {sessions.length === 0 && (
            <div className="p-6 text-center text-gray-500">
              No sessions found. Create your first session to get started.
            </div>
          )}
        </div>

        {/* Expanded Session Panel */}
        {expandedSessionId && (
          <div className="border-t border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Session Documents</h3>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Documents List */}
              <div className="lg:col-span-1">
                <div className="bg-gray-50 rounded-md p-4 max-h-80 overflow-auto">
                  {(sessionDocuments[expandedSessionId] || []).length === 0 ? (
                    <p className="text-sm text-gray-500">No documents uploaded for this session.</p>
                  ) : (
                    <ul className="divide-y divide-gray-200">
                      {(sessionDocuments[expandedSessionId] || []).map((doc) => (
                        <li key={doc.id} className="py-3 flex items-center justify-between">
                          <button
                            className={`text-left text-blue-700 hover:underline truncate ${selectedDocumentId === doc.id ? 'font-semibold' : ''}`}
                            title={doc.original_filename || doc.filename}
                            onClick={async () => {
                              setSelectedDocumentId(doc.id);
                              setPdfUrl(null);
                              try {
                                // Fetch PDF blob and create object URL for iframe
                                const blob = await api.admin.getDocumentFileBlob(doc.id);
                                const url = URL.createObjectURL(blob);
                                setPdfUrl(url);
                              } catch {
                                setError('Failed to open PDF');
                              }
                            }}
                          >
                            {doc.original_filename || doc.filename}
                          </button>
                          <button
                            className="text-red-600 hover:text-red-800 text-sm"
                            onClick={async () => {
                              if (!window.confirm('Delete this PDF from the session?')) return;
                              try {
                                await api.admin.deleteDocument(doc.id);
                                setSessionDocuments(prev => ({
                                  ...prev,
                                  [expandedSessionId]: (prev[expandedSessionId] || []).filter(d => d.id !== doc.id)
                                }));
                                // Update sessions list count
                                setSessions(prev => prev.map(s => s.id === expandedSessionId ? { ...s, document_count: Math.max((s.document_count || 1) - 1, 0) } : s));
                                setSuccess('Document deleted');
                                if (selectedDocumentId === doc.id) {
                                  setSelectedDocumentId(null);
                                  if (pdfUrl) URL.revokeObjectURL(pdfUrl);
                                  setPdfUrl(null);
                                }
                              } catch (e) {
                                setError('Failed to delete document');
                              }
                            }}
                          >
                            Delete
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {/* PDF Viewer */}
              <div className="lg:col-span-2">
                <div className="bg-white border rounded-md h-[600px] flex items-center justify-center">
                  {pdfUrl ? (
                    <iframe
                      title="PDF Viewer"
                      src={pdfUrl}
                      className="w-full h-full"
                    />
                  ) : (
                    <div className="text-gray-400">Select a document to preview</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Session Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Session</h3>
            <form onSubmit={handleCreateSession}>
              <div className="mb-4">
                <label htmlFor="sessionName" className="block text-sm font-medium text-gray-700 mb-2">
                  Session Name
                </label>
                <input
                  type="text"
                  id="sessionName"
                  value={sessionName}
                  onChange={(e) => setSessionName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  placeholder="e.g., Research Papers 2024"
                />
              </div>
              <div className="mb-4">
                <label htmlFor="chunkSize" className="block text-sm font-medium text-gray-700 mb-2">
                  Chunk Size
                </label>
                <input
                  type="number"
                  id="chunkSize"
                  value={chunkSize}
                  onChange={(e) => setChunkSize(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="100"
                  max="4000"
                />
              </div>
              <div className="mb-6">
                <label htmlFor="chunkOverlap" className="block text-sm font-medium text-gray-700 mb-2">
                  Chunk Overlap
                </label>
                <input
                  type="number"
                  id="chunkOverlap"
                  value={chunkOverlap}
                  onChange={(e) => setChunkOverlap(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  max="1000"
                />
              </div>
              <div className="mb-6">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="enableInternetSearch"
                    checked={enableInternetSearch}
                    onChange={(e) => setEnableInternetSearch(e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="enableInternetSearch" className="ml-2 block text-sm text-gray-700">
                    Enable Internet Search
                  </label>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  When enabled, the chatbot will search the internet for current information when needed
                </p>
              </div>

              {/* Session Admin selector */}
              <div className="mb-6">
                <label htmlFor="sessionAdmin" className="block text-sm font-medium text-gray-700 mb-2">
                  Session Admin (optional)
                </label>
                <select
                  id="sessionAdmin"
                  value={selectedSessionAdminId}
                  onChange={(e) => setSelectedSessionAdminId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Default to current admin</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.username} ({u.email}){u.is_admin ? ' [global admin]' : ''}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-500">If empty, the creating admin will be set as session admin.</p>
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Session'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Document Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Document</h3>
            <form onSubmit={handleUploadDocument}>
              <div className="mb-4">
                <label htmlFor="sessionSelect" className="block text-sm font-medium text-gray-700 mb-2">
                  Select Session
                </label>
                <select
                  id="sessionSelect"
                  value={selectedSession}
                  onChange={(e) => setSelectedSession(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Choose a session...</option>
                  {sessions.map((session) => (
                    <option key={session.id} value={session.id}>
                      {session.session_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-6">
                <label htmlFor="pdfFile" className="block text-sm font-medium text-gray-700 mb-2">
                  PDF File
                </label>
                <input
                  type="file"
                  id="pdfFile"
                  accept=".pdf"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowUploadModal(false);
                    setUploadFile(null);
                    setSelectedSession('');
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !uploadFile || !selectedSession}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MCP Tools Manager Modal */}
      {showToolsModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Manage MCP Tools</h3>
              <button
                onClick={() => {
                  setShowToolsModal(false);
                  setToolMode('list');
                  setToolForm({ name: '', tool_type: 'api', http_method: 'GET' });
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            {/* Tools list */}
            {toolMode === 'list' && (
              <div>
                <div className="flex justify-between mb-3">
                  <button
                    onClick={async () => {
                      if (!manageToolsSessionId) return;
                      try {
                        const data = await api.admin.listMcpTools(manageToolsSessionId);
                        setTools(data);
                      } catch {
                        setError('Failed to load tools');
                      }
                    }}
                    className="px-3 py-2 border rounded-md"
                  >
                    Refresh
                  </button>
                  <button
                    onClick={() => {
                      setToolForm({ name: '', tool_type: 'api', http_method: 'GET' });
                      setToolMode('create');
                    }}
                    className="px-3 py-2 bg-purple-600 text-white rounded-md"
                  >
                    + Add Tool
                  </button>
                </div>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {tools.map((t) => (
                      <tr key={t.id}>
                        <td className="px-4 py-2">{t.name}</td>
                        <td className="px-4 py-2">{t.tool_type}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          {t.tool_type === 'api' ? (
                            <>
                              <div><span className="font-medium">URL:</span> {t.api_url}</div>
                              <div><span className="font-medium">Method:</span> {t.http_method}</div>
                            </>
                          ) : (
                            <div className="truncate max-w-xs" title={t.function_code}>Python function</div>
                          )}
                        </td>
                        <td className="px-4 py-2 space-x-2">
                          <button
                            className="text-blue-600 hover:text-blue-800"
                            onClick={() => {
                              setToolForm({
                                id: t.id,
                                name: t.name,
                                tool_type: t.tool_type,
                                api_url: t.api_url,
                                http_method: t.http_method || 'GET',
                                function_code: t.function_code,
                                description: t.description,
                                params_docstring: t.params_docstring,
                                returns_docstring: t.returns_docstring,
                              });
                              setToolMode('edit');
                            }}
                          >
                            Edit
                          </button>
                          <button
                            className="text-red-600 hover:text-red-800"
                            onClick={async () => {
                              if (!window.confirm('Delete this tool?')) return;
                              try {
                                await api.admin.deleteMcpTool(t.id);
                                setTools(prev => prev.filter(x => x.id !== t.id));
                              } catch {
                                setError('Failed to delete tool');
                              }
                            }}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                    {tools.length === 0 && (
                      <tr>
                        <td className="px-4 py-6 text-center text-gray-500" colSpan={4}>No tools yet</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tool create/edit form */}
            {toolMode !== 'list' && (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  try {
                    if (!manageToolsSessionId) return;
                    if (toolMode === 'create') {
                      await api.admin.createMcpTool(manageToolsSessionId, {
                        name: toolForm.name,
                        tool_type: toolForm.tool_type,
                        api_url: toolForm.tool_type === 'api' ? toolForm.api_url : undefined,
                        http_method: toolForm.tool_type === 'api' ? (toolForm.http_method || 'GET') : undefined,
                        function_code: toolForm.tool_type === 'python_function' ? toolForm.function_code : undefined,
                        description: toolForm.description,
                        params_docstring: toolForm.params_docstring,
                        returns_docstring: toolForm.returns_docstring,
                      });
                    } else if (toolForm.id) {
                      await api.admin.updateMcpTool(toolForm.id, {
                        name: toolForm.name,
                        tool_type: toolForm.tool_type,
                        api_url: toolForm.tool_type === 'api' ? toolForm.api_url : undefined,
                        http_method: toolForm.tool_type === 'api' ? (toolForm.http_method || 'GET') : undefined,
                        function_code: toolForm.tool_type === 'python_function' ? toolForm.function_code : undefined,
                        description: toolForm.description,
                        params_docstring: toolForm.params_docstring,
                        returns_docstring: toolForm.returns_docstring,
                      });
                    }
                    // refresh list and go back
                    const data = await api.admin.listMcpTools(manageToolsSessionId);
                    setTools(data);
                    setToolMode('list');
                    setToolForm({ name: '', tool_type: 'api', http_method: 'GET' });
                  } catch (err: any) {
                    setError(err.response?.data?.detail || 'Failed to save tool');
                  }
                }}
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      value={toolForm.name}
                      onChange={(e) => setToolForm({ ...toolForm, name: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                    <select
                      value={toolForm.tool_type}
                      onChange={(e) => setToolForm({ ...toolForm, tool_type: e.target.value as 'api' | 'python_function' })}
                      className="w-full px-3 py-2 border rounded-md"
                    >
                      <option value="api">API</option>
                      <option value="python_function">Python Function</option>
                    </select>
                  </div>

                  {toolForm.tool_type === 'api' && (
                    <>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">API URL</label>
                        <input
                          type="url"
                          value={toolForm.api_url || ''}
                          onChange={(e) => setToolForm({ ...toolForm, api_url: e.target.value })}
                          className="w-full px-3 py-2 border rounded-md"
                          placeholder="https://example.com/endpoint"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">HTTP Method</label>
                        <select
                          value={toolForm.http_method || 'GET'}
                          onChange={(e) => setToolForm({ ...toolForm, http_method: e.target.value })}
                          className="w-full px-3 py-2 border rounded-md"
                        >
                          <option>GET</option>
                          <option>POST</option>
                          <option>PUT</option>
                          <option>DELETE</option>
                        </select>
                      </div>
                    </>
                  )}

                  {toolForm.tool_type === 'python_function' && (
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Function Code</label>
                      <textarea
                        value={toolForm.function_code || ''}
                        onChange={(e) => setToolForm({ ...toolForm, function_code: e.target.value })}
                        className="w-full px-3 py-2 border rounded-md font-mono"
                        rows={6}
                        placeholder={'def my_tool(param1: str) -> str:\n    """Describe params and return here"""\n    return "result"'}
                        required
                      />
                    </div>
                  )}

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                      value={toolForm.description || ''}
                      onChange={(e) => setToolForm({ ...toolForm, description: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md"
                      rows={3}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Params Docstring</label>
                    <textarea
                      value={toolForm.params_docstring || ''}
                      onChange={(e) => setToolForm({ ...toolForm, params_docstring: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Returns Docstring</label>
                    <textarea
                      value={toolForm.returns_docstring || ''}
                      onChange={(e) => setToolForm({ ...toolForm, returns_docstring: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md"
                      rows={3}
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setToolMode('list');
                      setToolForm({ name: '', tool_type: 'api', http_method: 'GET' });
                    }}
                    className="px-4 py-2 border rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-purple-600 text-white rounded-md"
                  >
                    {toolMode === 'create' ? 'Create Tool' : 'Save Changes'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;