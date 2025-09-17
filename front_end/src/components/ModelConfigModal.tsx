import React, { useEffect, useState } from 'react';

export type Provider = 'groq' | 'openai' | 'ollama';

export interface ModelConfigForm {
  model_provider: Provider;
  model_name: string;
  model_temperature: number;
  model_max_output_tokens?: number; // normalized to undefined when empty
  model_base_url?: string; // for Ollama; normalized to undefined when empty
  model_api_key?: string; // write-only for OpenAI/Groq; normalized to undefined when empty
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (payload: ModelConfigForm) => Promise<void> | void;
  initial?: Partial<ModelConfigForm>;
}

const providerOptions: { label: string; value: Provider }[] = [
  { label: 'Groq', value: 'groq' },
  { label: 'OpenAI', value: 'openai' },
  { label: 'Ollama', value: 'ollama' },
];

const ModelConfigModal: React.FC<Props> = ({ open, onClose, onSave, initial }) => {
  const [form, setForm] = useState<ModelConfigForm>({
    model_provider: 'groq',
    model_name: 'llama-3.3-70b-versatile',
    model_temperature: 0.1,
    model_max_output_tokens: undefined,
    model_base_url: '',
    model_api_key: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (open) {
      setError('');
      setSaving(false);
      setForm({
        model_provider: (initial?.model_provider as Provider) || 'groq',
        model_name: initial?.model_name || 'llama-3.3-70b-versatile',
        model_temperature: initial?.model_temperature ?? 0.1,
        model_max_output_tokens: initial?.model_max_output_tokens ?? undefined,
        model_base_url: initial?.model_base_url || '',
        model_api_key: '', // we never prefill API keys
      });
    }
  }, [open, initial]);

  if (!open) return null;

  const showApiKey = form.model_provider === 'openai' || form.model_provider === 'groq';
  const showBaseUrl = form.model_provider === 'ollama';

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload: ModelConfigForm = { ...form };
      // Normalize empties to match ModelConfigUpdate
      if (!showApiKey || !payload.model_api_key) delete payload.model_api_key;
      if (!showBaseUrl || !payload.model_base_url) delete payload.model_base_url;
      if (payload.model_max_output_tokens === undefined || payload.model_max_output_tokens === null) {
        delete payload.model_max_output_tokens;
      }
      await onSave(payload);
      onClose();
    } catch (e: any) {
      setError(e?.message || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Model Configuration</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mx-6 mt-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-md">{error}</div>
        )}

        <form onSubmit={handleSave} className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
            <select
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.model_provider}
              onChange={(e) => setForm((f) => ({ ...f, model_provider: e.target.value as Provider }))}
            >
              {providerOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model name</label>
            <input
              type="text"
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={form.model_provider === 'groq' ? 'llama-3.3-70b-versatile' : form.model_provider === 'openai' ? 'gpt-4o-mini' : 'llama3'
              }
              value={form.model_name}
              onChange={(e) => setForm((f) => ({ ...f, model_name: e.target.value }))}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
              <input
                type="number"
                step="0.01"
                min={0}
                max={2}
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.model_temperature}
                onChange={(e) => setForm((f) => ({ ...f, model_temperature: parseFloat(e.target.value) }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max output tokens</label>
              <input
                type="number"
                min={1}
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.model_max_output_tokens ?? ''}
                onChange={(e) => {
                  const v = e.target.value;
                  setForm((f) => ({ ...f, model_max_output_tokens: v === '' ? undefined : parseInt(v, 10) }));
                }}
                placeholder="Optional"
              />
            </div>
          </div>

          {showBaseUrl && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ollama base URL</label>
              <input
                type="text"
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.model_base_url ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, model_base_url: e.target.value }))}
                placeholder="http://localhost:11434"
              />
            </div>
          )}

          {showApiKey && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API key</label>
              <input
                type="password"
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.model_api_key || ''}
                onChange={(e) => setForm((f) => ({ ...f, model_api_key: e.target.value }))}
                placeholder={form.model_provider === 'groq' ? 'GROQ_API_KEY' : 'OPENAI_API_KEY'}
              />
              <p className="mt-1 text-xs text-gray-500">This is write-only and won’t be shown again.</p>
            </div>
          )}

          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ModelConfigModal;