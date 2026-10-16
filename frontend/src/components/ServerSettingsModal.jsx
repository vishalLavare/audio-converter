import React, { useState, useEffect } from 'react';
import { Settings, Server, CheckCircle2, AlertCircle, RefreshCw, X, Cloud, Laptop, Smartphone } from 'lucide-react';
import { getSavedServerUrl, setCustomServerUrl, testServerConnection, getBaseUrl, DEFAULT_CLOUD_BACKEND } from '../api';

export default function ServerSettingsModal({ isOpen, onClose }) {
  const [serverUrl, setServerUrl] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null); // { ok: boolean, message: string }
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setServerUrl(getSavedServerUrl() || getBaseUrl().replace(/\/api$/, ''));
      setTestResult(null);
      setSaveSuccess(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      await testServerConnection(serverUrl);
      setTestResult({ ok: true, message: 'Successfully connected to backend server!' });
    } catch (err) {
      setTestResult({ ok: false, message: err.message || 'Connection failed' });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    setCustomServerUrl(serverUrl);
    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
      onClose();
    }, 900);
  };

  const handleReset = () => {
    setCustomServerUrl('');
    setServerUrl(getBaseUrl().replace(/\/api$/, ''));
    setTestResult({ ok: true, message: 'Reset to default backend configuration.' });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-5 text-slate-200">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Backend Server URL</h3>
              <p className="text-xs text-slate-400">Configure where your mobile app connects</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300">
            API Host / IP Address
          </label>
          <div className="relative">
            <input
              type="text"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
              placeholder="e.g. http://192.168.1.15:8000 or https://api.mysite.com"
              className="w-full px-4 py-3 bg-slate-950/80 border border-slate-800 focus:border-purple-500 rounded-xl text-sm font-mono text-slate-100 placeholder:text-slate-600 focus:outline-none transition-colors"
            />
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              type="button"
              onClick={() => {
                setServerUrl(DEFAULT_CLOUD_BACKEND);
                setTestResult(null);
              }}
              className="px-2.5 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-300 text-[11px] font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Cloud className="w-3.5 h-3.5" />
              <span>Render Cloud</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setServerUrl('http://localhost:8000');
                setTestResult(null);
              }}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[11px] font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Laptop className="w-3.5 h-3.5" />
              <span>Localhost (8000)</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setServerUrl('http://10.0.2.2:8000');
                setTestResult(null);
              }}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[11px] font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Smartphone className="w-3.5 h-3.5" />
              <span>Android Emulator</span>
            </button>
          </div>
          <p className="text-[11px] text-slate-500">
            For live cloud: use <code className="text-purple-400">{DEFAULT_CLOUD_BACKEND}</code>.
            <br />
            For local Wi-Fi testing: use your PC's IP (e.g. <code className="text-slate-400">http://192.168.x.x:8000</code>).
          </p>
        </div>

        {testResult && (
          <div
            className={`p-3 rounded-xl border text-xs flex items-center gap-2.5 ${
              testResult.ok
                ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                : 'bg-red-950/40 border-red-500/40 text-red-300'
            }`}
          >
            {testResult.ok ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            )}
            <span className="truncate">{testResult.message}</span>
          </div>
        )}

        {saveSuccess && (
          <div className="p-3 bg-emerald-950/50 border border-emerald-500/50 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Settings saved successfully!</span>
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <button
            type="button"
            onClick={handleTest}
            disabled={testing}
            className="flex-1 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-[0.98] text-xs font-semibold text-slate-200 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${testing ? 'animate-spin' : ''}`} />
            <span>{testing ? 'Testing...' : 'Test Connection'}</span>
          </button>

          <button
            type="button"
            onClick={handleSave}
            className="flex-1 py-2.5 px-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 active:scale-[0.98] text-xs font-semibold text-white shadow-lg shadow-purple-500/20 transition-all cursor-pointer"
          >
            Save & Apply
          </button>
        </div>

        <div className="text-center pt-1">
          <button
            type="button"
            onClick={handleReset}
            className="text-[11px] text-slate-500 hover:text-slate-400 underline cursor-pointer"
          >
            Reset to Default
          </button>
        </div>
      </div>
    </div>
  );
}
