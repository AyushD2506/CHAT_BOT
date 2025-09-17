import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ChatSession, Document, MCPTool } from '../types';
import RowActionBar from '../components/RowActionBar';
import ModelConfigModal, { ModelConfigForm } from '../components/ModelConfigModal';

const SessionAdminDashboard: React.FC = () => {
  // Sessions/table state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Expanded session panel state
  const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null);
  const [sessionDocuments, setSessionDocuments] = useState<Record<string, Document[]>>({});
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedSessionForUpload, setSelectedSessionForUpload] = useState<string>('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Tools modal state (mirror Admin UI but use sessionAdmin endpoints)
  const [showToolsModal, setShowToolsModal] = useState(false);
  const [manageToolsSessionId, setManageToolsSessionId] = useState<string | null>(null);
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [toolMode, setToolMode] = useState<'list' | 'create' | 'edit'>('list');
  const [toolForm, setToolForm] = useState<{
    id?: string;
    name: string;
    tool_type: 'api' | 'python_function';
    api_url?: string;
    http_method?: string;
    function_code?: string;
    description?: string;
    params_docstring?: string;
    returns_docstring?: string;
  }>({ name: '', tool_type: 'api', http_method: 'GET' });

  // Model config modal state
  const [showModelConfig, setShowModelConfig] = useState(false);
  const [modelConfigSessionId, setModelConfigSessionId] = useState<string | null>(null);
  const [modelConfigInitial, setModelConfigInitial] = useState<Partial<ModelConfigForm>>({});

  // Config quick-edit state (inline in table or panel not required; we mirror Admin actions for toggle internet)

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await api.sessionAdmin.listMySessions();
      setSessions(data);
    } catch (e) {
      setError('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  // Auto clear toasts
  useEffect(() => {
    if (error || success) {
      const t = setTimeout(() => { setError(''); setSuccess(''); }, 3000);
      return () => clearTimeout(t);
    }
  }, [error, success]);

  const openSessionPanel = async (sessionId: string) => {
    const nextId = expandedSessionId === sessionId ? null : sessionId;
    setExpandedSessionId(nextId);
    setSelectedDocumentId(null);
    setPdfUrl(null);
    if (nextId) {
      try {
        const docs = await api.sessionAdmin.listDocuments(sessionId);
        setSessionDocuments(prev => ({ ...prev, [sessionId]: docs }));
      } catch {
        setError('Failed to load session documents');
      }
    }
  };

  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !selectedSessionForUpload) return;

    setLoading(true);
    setError('');

    try {
      const doc = await api.sessionAdmin.uploadDocument(selectedSessionForUpload, uploadFile);
      setShowUploadModal(false);
      setUploadFile(null);
      setSuccess('Document uploaded successfully!');

      // Update expanded panel docs if matching
      setSessionDocuments(prev => ({
        ...prev,
        [selectedSessionForUpload]: [doc, ...(prev[selectedSessionForUpload] || [])]
      }));

      // Update sessions list count
      setSessions(prev => prev.map(s => s.id === selectedSessionForUpload ? { ...s, document_count: (s.document_count || 0) + 1 } : s));

      setSelectedSessionForUpload('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setLoading(false);
    }
  };

  const toggleInternetSearch = async (sessionId: string) => {
    const target = sessions.find(s => s.id === sessionId);
    if (!target) return;
    try {
      const updated = await api.sessionAdmin.updateSession(sessionId, { enable_internet_search: !target.enable_internet_search });
      setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, enable_internet_search: updated.enable_internet_search } : s));
      setSuccess(`Internet search ${!target.enable_internet_search ? 'enabled' : 'disabled'} for session`);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to update internet search setting');
    }
  };

  const deleteSession = async (sessionId: string) => {
    if (!window.confirm('Are you sure you want to delete this session? This will delete all associated documents and messages.')) return;
    setLoading(true);
    try {
      await api.sessionAdmin.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (expandedSessionId === sessionId) {
        setExpandedSessionId(null);
        setSessionDocuments(prev => { const cp = { ...prev }; delete cp[sessionId]; return cp; });
        setSelectedDocumentId(null);
        if (pdfUrl) URL.revokeObjectURL(pdfUrl);
        setPdfUrl(null);
      }
      setSuccess('Session deleted successfully!');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to delete session');
    } finally {
      setLoading(false);
    }
  };

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
        <h1 className="text-2xl font-bold text-gray-900">Session Admin Dashboard</h1>
        <div className="flex flex-wrap items-center gap-2">
          {/* Upload Document button only (no Create Session, no Analytics) */}
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

      {/* Sessions List (table like Admin) */}
      <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-100">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">My Chat Sessions</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Session Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Documents</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chunk Settings</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Internet Search</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {sessions.map((session) => (
                <tr key={session.id} className="hover:bg-gray-50/60">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{session.session_name}</div>
                    <div className="text-xs text-gray-500">ID: {session.id.substring(0, 8)}...</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{session.document_count || 0}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    Size: {session.chunk_size}<br />
                    Overlap: {session.chunk_overlap}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      session.enable_internet_search ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {session.enable_internet_search ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{new Date(session.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      session.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {session.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm font-medium">
                    <RowActionBar
                      disabled={loading}
                      isExpanded={expandedSessionId === session.id}
                      onToggleExpand={() => openSessionPanel(session.id)}
                      isActive={session.is_active}
                      onToggleActive={async () => {
                        try {
                          const updated = await api.sessionAdmin.updateSession(session.id, { is_active: !session.is_active });
                          setSessions(prev => prev.map(s => s.id === session.id ? { ...s, is_active: updated.is_active } : s));
                          setSuccess(`Session ${!session.is_active ? 'activated' : 'disabled'} successfully`);
                        } catch (e: any) {
                          setError(e.response?.data?.detail || 'Failed to update session status');
                        }
                      }}
                      isSearchEnabled={session.enable_internet_search}
                      onToggleSearch={() => toggleInternetSearch(session.id)}
                      onUploadPDF={() => {
                        setSelectedSessionForUpload(session.id);
                        setShowUploadModal(true);
                      }}
                      onManageTools={async () => {
                        setExpandedSessionId(session.id);
                        setManageToolsSessionId(session.id);
                        setShowToolsModal(true);
                        try {
                          const data = await api.sessionAdmin.listTools(session.id);
                          setTools(data);
                        } catch {
                          setError('Failed to load tools');
                        }
                      }}
                      onConfigureModel={() => {
                        setModelConfigSessionId(session.id);
                        setModelConfigInitial({
                          model_provider: (session.model_provider as any) || undefined,
                          model_name: session.model_name || undefined,
                          model_temperature: session.model_temperature ?? undefined,
                          model_max_output_tokens: session.model_max_output_tokens ?? undefined,
                          model_base_url: session.model_base_url || undefined,
                        });
                        setShowModelConfig(true);
                      }}
                      onDelete={() => deleteSession(session.id)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {sessions.length === 0 && (
            <div className="p-6 text-center text-gray-500">No sessions assigned to you.</div>
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
                                const blob = await api.sessionAdmin.getDocumentFileBlob(doc.id);
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
                                await api.sessionAdmin.deleteDocument(doc.id);
                                setSessionDocuments(prev => ({
                                  ...prev,
                                  [expandedSessionId]: (prev[expandedSessionId] || []).filter(d => d.id !== doc.id)
                                }));
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
                    <iframe title="PDF Viewer" src={pdfUrl} className="w-full h-full" />
                  ) : (
                    <div className="text-gray-400">Select a document to preview</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Upload Document Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Document</h3>
            <form onSubmit={handleUploadDocument}>
              <div className="mb-4">
                <label htmlFor="sessionSelect" className="block text-sm font-medium text-gray-700 mb-2">Select Session</label>
                <select
                  id="sessionSelect"
                  value={selectedSessionForUpload}
                  onChange={(e) => setSelectedSessionForUpload(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Choose a session...</option>
                  {sessions.map(s => (
                    <option key={s.id} value={s.id}>{s.session_name}</option>
                  ))}
                </select>
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">PDF File</label>
                <input type="file" accept="application/pdf" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} />
              </div>
              <div className="flex justify-end space-x-3">
                <button type="button" onClick={() => { setShowUploadModal(false); setUploadFile(null); }} className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
                <button type="submit" disabled={loading || !uploadFile || !selectedSessionForUpload} className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50">
                  {loading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Model Config Modal */}
      {showModelConfig && (
        <ModelConfigModal
          open={showModelConfig}
          onClose={() => setShowModelConfig(false)}
          initial={modelConfigInitial}
          onSave={async (payload: ModelConfigForm) => {
            if (!modelConfigSessionId) return;
            try {
              const updated = await api.sessionAdmin.updateSession(modelConfigSessionId, payload);
              setSessions(prev => prev.map(s => s.id === modelConfigSessionId ? { ...s, ...updated } : s));
              setSuccess('Model configuration updated');
            } catch (e: any) {
              setError(e.response?.data?.detail || 'Failed to update model configuration');
              throw e;
            }
          }}
        />
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
                        const data = await api.sessionAdmin.listTools(manageToolsSessionId);
                        setTools(data);
                      } catch {
                        setError('Failed to refresh tools');
                      }
                    }}
                    className="text-sm text-indigo-600 hover:text-indigo-800"
                  >
                    Refresh
                  </button>
                  <button
                    onClick={() => setToolMode('create')}
                    className="text-sm text-white bg-indigo-600 hover:bg-indigo-700 px-3 py-1 rounded"
                  >
                    + Create Tool
                  </button>
                </div>
                <ul className="divide-y">
                  {tools.map(t => (
                    <li key={t.id} className="py-2 flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">{t.name} <span className="text-gray-500">({t.tool_type})</span></div>
                        {t.description && <div className="text-xs text-gray-500">{t.description}</div>}
                      </div>
                      <div className="space-x-3 text-sm">
                        <button
                          onClick={() => {
                            setToolMode('edit');
                            setToolForm({
                              id: t.id,
                              name: t.name,
                              tool_type: t.tool_type as 'api' | 'python_function',
                              api_url: t.api_url || undefined,
                              http_method: t.http_method || 'GET',
                              function_code: t.function_code || undefined,
                              description: t.description || undefined,
                              params_docstring: t.params_docstring || undefined,
                              returns_docstring: t.returns_docstring || undefined,
                            });
                          }}
                          className="text-indigo-600 hover:text-indigo-800"
                        >
                          Edit
                        </button>
                        <button
                          onClick={async () => {
                            if (!manageToolsSessionId) return;
                            if (!window.confirm('Delete this tool?')) return;
                            try {
                              await api.sessionAdmin.deleteTool(manageToolsSessionId, t.id);
                              setTools(prev => prev.filter(x => x.id !== t.id));
                              setSuccess('Tool deleted');
                            } catch (e: any) {
                              setError(e.response?.data?.detail || 'Failed to delete tool');
                            }
                          }}
                          className="text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </div>
                    </li>
                  ))}
                  {tools.length === 0 && <li className="py-2 text-sm text-gray-500">No tools</li>}
                </ul>
              </div>
            )}

            {/* Create tool */}
            {toolMode === 'create' && (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (!manageToolsSessionId) return;
                  try {
                    const created = await api.sessionAdmin.createTool(manageToolsSessionId, {
                      name: toolForm.name,
                      tool_type: toolForm.tool_type,
                      api_url: toolForm.tool_type === 'api' ? toolForm.api_url : undefined,
                      http_method: toolForm.tool_type === 'api' ? (toolForm.http_method || 'GET') : undefined,
                      function_code: toolForm.tool_type === 'python_function' ? toolForm.function_code : undefined,
                      description: toolForm.description,
                      params_docstring: toolForm.params_docstring,
                      returns_docstring: toolForm.returns_docstring,
                    });
                    setTools(prev => [created, ...prev]);
                    setSuccess('Tool created');
                    setToolMode('list');
                    setToolForm({ name: '', tool_type: 'api', http_method: 'GET' });
                  } catch (e: any) {
                    setError(e.response?.data?.detail || 'Failed to create tool');
                  }
                }}
                className="space-y-3"
              >
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-gray-700">Name</label>
                    <input className="mt-1 w-full rounded-md border-gray-300" value={toolForm.name} onChange={e => setToolForm(prev => ({ ...prev, name: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-700">Type</label>
                    <select className="mt-1 w-full rounded-md border-gray-300" value={toolForm.tool_type} onChange={e => setToolForm(prev => ({ ...prev, tool_type: e.target.value as any }))}>
                      <option value="api">API</option>
                      <option value="python_function">Python Function</option>
                    </select>
                  </div>
                </div>
                {toolForm.tool_type === 'api' ? (
                  <>
                    <div>
                      <label className="block text-sm text-gray-700">HTTP Method</label>
                      <select className="mt-1 w-full rounded-md border-gray-300" value={toolForm.http_method} onChange={e => setToolForm(prev => ({ ...prev, http_method: e.target.value }))}>
                        <option>GET</option>
                        <option>POST</option>
                        <option>PUT</option>
                        <option>DELETE</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-700">API URL</label>
                      <input className="mt-1 w-full rounded-md border-gray-300" placeholder="https://api.example.com/endpoint" value={toolForm.api_url || ''} onChange={e => setToolForm(prev => ({ ...prev, api_url: e.target.value }))} />
                    </div>
                  </>
                ) : (
                  <div>
                    <label className="block text-sm text-gray-700">Function Code</label>
                    <textarea className="mt-1 w-full rounded-md border-gray-300" rows={6} placeholder="def my_tool(...):\n    return ..." value={toolForm.function_code || ''} onChange={e => setToolForm(prev => ({ ...prev, function_code: e.target.value }))} />
                  </div>
                )}
                <div>
                  <label className="block text-sm text-gray-700">Description</label>
                  <input className="mt-1 w-full rounded-md border-gray-300" value={toolForm.description || ''} onChange={e => setToolForm(prev => ({ ...prev, description: e.target.value }))} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-gray-700">Params Docstring</label>
                    <textarea className="mt-1 w-full rounded-md border-gray-300" rows={3} value={toolForm.params_docstring || ''} onChange={e => setToolForm(prev => ({ ...prev, params_docstring: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-700">Returns Docstring</label>
                    <textarea className="mt-1 w-full rounded-md border-gray-300" rows={3} value={toolForm.returns_docstring || ''} onChange={e => setToolForm(prev => ({ ...prev, returns_docstring: e.target.value }))} />
                  </div>
                </div>
                <div className="flex justify-end space-x-3">
                  <button type="button" onClick={() => { setToolMode('list'); setToolForm({ name: '', tool_type: 'api', http_method: 'GET' }); }} className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
                  <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">Create</button>
                </div>
              </form>
            )}

            {/* Edit tool */}
            {toolMode === 'edit' && toolForm.id && (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (!manageToolsSessionId || !toolForm.id) return;
                  try {
                    const updated = await api.sessionAdmin.updateTool(manageToolsSessionId, toolForm.id, {
                      name: toolForm.name,
                      tool_type: toolForm.tool_type,
                      api_url: toolForm.tool_type === 'api' ? toolForm.api_url : undefined,
                      http_method: toolForm.tool_type === 'api' ? (toolForm.http_method || 'GET') : undefined,
                      function_code: toolForm.tool_type === 'python_function' ? toolForm.function_code : undefined,
                      description: toolForm.description,
                      params_docstring: toolForm.params_docstring,
                      returns_docstring: toolForm.returns_docstring,
                    });
                    setTools(prev => prev.map(t => t.id === updated.id ? updated : t));
                    setSuccess('Tool updated');
                    setToolMode('list');
                    setToolForm({ name: '', tool_type: 'api', http_method: 'GET' });
                  } catch (e: any) {
                    setError(e.response?.data?.detail || 'Failed to update tool');
                  }
                }}
                className="space-y-3"
              >
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-gray-700">Name</label>
                    <input className="mt-1 w-full rounded-md border-gray-300" value={toolForm.name} onChange={e => setToolForm(prev => ({ ...prev, name: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-700">Type</label>
                    <select className="mt-1 w-full rounded-md border-gray-300" value={toolForm.tool_type} onChange={e => setToolForm(prev => ({ ...prev, tool_type: e.target.value as any }))}>
                      <option value="api">API</option>
                      <option value="python_function">Python Function</option>
                    </select>
                  </div>
                </div>
                {toolForm.tool_type === 'api' ? (
                  <>
                    <div>
                      <label className="block text-sm text-gray-700">HTTP Method</label>
                      <select className="mt-1 w-full rounded-md border-gray-300" value={toolForm.http_method} onChange={e => setToolForm(prev => ({ ...prev, http_method: e.target.value }))}>
                        <option>GET</option>
                        <option>POST</option>
                        <option>PUT</option>
                        <option>DELETE</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-700">API URL</label>
                      <input className="mt-1 w-full rounded-md border-gray-300" placeholder="https://api.example.com/endpoint" value={toolForm.api_url || ''} onChange={e => setToolForm(prev => ({ ...prev, api_url: e.target.value }))} />
                    </div>
                  </>
                ) : (
                  <div>
                    <label className="block text-sm text-gray-700">Function Code</label>
                    <textarea className="mt-1 w-full rounded-md border-gray-300" rows={6} placeholder="def my_tool(...):\n    return ..." value={toolForm.function_code || ''} onChange={e => setToolForm(prev => ({ ...prev, function_code: e.target.value }))} />
                  </div>
                )}
                <div>
                  <label className="block text-sm text-gray-700">Description</label>
                  <input className="mt-1 w-full rounded-md border-gray-300" value={toolForm.description || ''} onChange={e => setToolForm(prev => ({ ...prev, description: e.target.value }))} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-gray-700">Params Docstring</label>
                    <textarea className="mt-1 w-full rounded-md border-gray-300" rows={3} value={toolForm.params_docstring || ''} onChange={e => setToolForm(prev => ({ ...prev, params_docstring: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-700">Returns Docstring</label>
                    <textarea className="mt-1 w-full rounded-md border-gray-300" rows={3} value={toolForm.returns_docstring || ''} onChange={e => setToolForm(prev => ({ ...prev, returns_docstring: e.target.value }))} />
                  </div>
                </div>
                <div className="flex justify-end space-x-3">
                  <button type="button" onClick={() => { setToolMode('list'); setToolForm({ name: '', tool_type: 'api', http_method: 'GET' }); }} className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
                  <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">Save</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionAdminDashboard;