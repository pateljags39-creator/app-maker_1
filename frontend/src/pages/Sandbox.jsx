import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { PlayCircle, StopCircle, RefreshCw, Maximize2, ExternalLink, Terminal, AlertTriangle, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

function fmtAgo(ts) {
  if (!ts) return '';
  const sec = Math.max(0, Math.floor((Date.now() / 1000) - ts));
  if (sec < 60) return `${sec}s ago`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  return `${Math.floor(sec / 3600)}h ago`;
}

export default function SandboxPage() {
  const { project } = useOutletContext();
  const [status, setStatus] = useState({ running: false });
  const [busy, setBusy] = useState(false);
  const [iframeKey, setIframeKey] = useState(0);
  const [logs, setLogs] = useState('');
  const [showLogs, setShowLogs] = useState(false);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);
  const iframeRef = useRef(null);

  const loadStatus = useCallback(async () => {
    try {
      const r = await api.sandboxStatus(project.id);
      setStatus(r);
    } catch (e) {
      // ignore — keeps last state
    }
  }, [project.id]);

  const loadLogs = useCallback(async () => {
    try {
      const r = await api.sandboxLogs(project.id, 200);
      setLogs(r?.tail || '');
    } catch (e) { /* ignore */ }
  }, [project.id]);

  useEffect(() => {
    loadStatus();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [loadStatus]);

  useEffect(() => {
    if (status.running) {
      if (!pollRef.current) {
        pollRef.current = setInterval(() => { loadStatus(); }, 5000);
      }
    } else if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, [status.running, loadStatus]);

  const start = async () => {
    setError(null);
    try {
      setBusy(true);
      await api.sandboxStart(project.id);
      toast.success('Sandbox started');
      await loadStatus();
      setIframeKey(k => k + 1);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || 'Failed to start sandbox';
      setError(msg);
      toast.error(msg.slice(0, 200));
      // Auto-load logs so the user can see what blew up
      await loadLogs();
      setShowLogs(true);
    } finally { setBusy(false); }
  };

  const stop = async () => {
    try {
      setBusy(true);
      await api.sandboxStop(project.id);
      toast.success('Sandbox stopped');
      await loadStatus();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed to stop');
    } finally { setBusy(false); }
  };

  const reload = () => {
    setIframeKey(k => k + 1);
  };

  const openInNewTab = () => {
    const url = api.sandboxIframeSrc(project.id);
    window.open(url, '_blank', 'noopener');
  };

  const iframeSrc = status.running ? api.sandboxIframeSrc(project.id) : null;

  return (
    <div className="space-y-4" data-testid="sandbox-page">
      <div className="surface-1 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-[hsl(var(--primary))]" />
              <div className="text-lg font-semibold">Live Sandbox</div>
            </div>
            <div className="mt-1 text-sm text-muted-foreground max-w-2xl">
              Run the generated app right here so you can click around and see how it behaves before
              exporting. Requires a successful build (frontend <code>dist/</code> must exist).
            </div>
          </div>
          <div className="flex items-center gap-2">
            {status.running ? (
              <>
                <span className="rounded-full px-2.5 py-1 text-xs font-mono bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  running · port {status.port}
                </span>
                <button
                  onClick={reload}
                  disabled={busy}
                  data-testid="sandbox-reload-btn"
                  className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs hover:bg-accent disabled:opacity-50"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Reload
                </button>
                <button
                  onClick={openInNewTab}
                  data-testid="sandbox-open-newtab-btn"
                  className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs hover:bg-accent"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open in new tab
                </button>
                <button
                  onClick={stop}
                  disabled={busy}
                  data-testid="sandbox-stop-btn"
                  className="inline-flex items-center gap-1.5 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-1.5 text-xs text-red-300 hover:bg-red-500/20 disabled:opacity-50"
                >
                  <StopCircle className="h-3.5 w-3.5" />
                  Stop
                </button>
              </>
            ) : (
              <button
                onClick={start}
                disabled={busy}
                data-testid="sandbox-start-btn"
                className="inline-flex items-center gap-1.5 rounded-md bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] px-3 py-1.5 text-sm font-medium hover:opacity-90 disabled:opacity-50"
              >
                <PlayCircle className="h-4 w-4" />
                {busy ? 'Starting…' : 'Run Demo'}
              </button>
            )}
          </div>
        </div>
        {status.running && (
          <div className="mt-3 text-xs text-muted-foreground font-mono flex items-center gap-3 flex-wrap">
            <span>started {fmtAgo(status.started_at)}</span>
            <span>·</span>
            <span>last activity {fmtAgo(status.last_used)}</span>
            <span>·</span>
            <span>auto-stops after 15 min idle</span>
          </div>
        )}
      </div>

      {error && (
        <div className="surface-1 border-red-500/30 bg-red-500/5 p-4" data-testid="sandbox-error">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
            <div>
              <div className="text-sm font-semibold text-red-300">Sandbox couldn't start</div>
              <pre className="mt-1 text-xs whitespace-pre-wrap font-mono text-red-200/90">{error}</pre>
              <div className="mt-2 text-xs text-muted-foreground">
                Common causes: frontend hasn't been built yet (run <strong>Build</strong> first), backend has
                a syntax error, or a port is already in use.
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="surface-1 overflow-hidden">
        <div className="px-4 py-2 border-b border-border flex items-center justify-between">
          <div className="text-xs text-muted-foreground font-mono">
            {iframeSrc ? iframeSrc : 'sandbox not running'}
          </div>
          {iframeSrc && (
            <button
              onClick={() => iframeRef.current?.requestFullscreen?.()}
              className="text-muted-foreground hover:text-foreground"
              title="Fullscreen"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          )}
        </div>
        <div className="bg-black/30" style={{ minHeight: '70vh' }}>
          {iframeSrc ? (
            <iframe
              ref={iframeRef}
              key={iframeKey}
              src={iframeSrc}
              title="Sandbox"
              data-testid="sandbox-iframe"
              className="w-full"
              style={{ height: '70vh', border: 0, background: 'white' }}
              sandbox="allow-forms allow-scripts allow-same-origin allow-popups allow-modals"
            />
          ) : (
            <div className="flex h-[70vh] items-center justify-center">
              <div className="text-center max-w-md px-6">
                <PlayCircle className="h-12 w-12 mx-auto text-muted-foreground/40" />
                <div className="mt-3 text-sm font-semibold">No sandbox running</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  Click <strong>Run Demo</strong> above to spawn the generated app and view it here.
                  The cockpit proxies HTTP calls to the generated backend so the frontend works
                  end-to-end without any further configuration.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="surface-1">
        <button
          onClick={() => { setShowLogs(v => !v); if (!showLogs) loadLogs(); }}
          className="w-full px-4 py-2 text-left text-xs text-muted-foreground hover:text-foreground flex items-center gap-2"
        >
          <Terminal className="h-3.5 w-3.5" />
          <span>{showLogs ? 'Hide' : 'Show'} sandbox backend logs</span>
        </button>
        {showLogs && (
          <div className="border-t border-border">
            <div className="px-4 py-2 flex items-center justify-between">
              <div className="text-xs font-mono text-muted-foreground">last 200 lines</div>
              <button
                onClick={loadLogs}
                className="text-xs text-[hsl(var(--link))] hover:underline"
              >
                Refresh
              </button>
            </div>
            <pre
              data-testid="sandbox-logs"
              className="px-4 py-3 text-[11px] font-mono bg-black/40 text-emerald-100/90 overflow-auto"
              style={{ maxHeight: 320 }}
            >
              {logs || '(no logs yet — start the sandbox to see output)'}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
